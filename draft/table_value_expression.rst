DEP XXXX: Supoort for Table Expressions in the Django ORM
=========================================================

:DEP: XXXX
:Author: Pravin Kamble
:Implementation Team: Pravin Kamble
:Shepherd: Jacob Walls
:Status: Draft
:Type: Feature
:Created: 2026-05-30

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

This DEP proposes adding ORM support for table expressions: query sources that
can appear in SQL ``FROM`` or ``JOIN`` clauses and expose columns that can be
referenced by the rest of the queryset.

The first motivating cases are set-returning functions, multi-column
table-valued functions, and querysets or subqueries used as table sources.

The proposal is intentionally focused on the problem and desired ORM behavior.
The exact internal API is still open.

Motivation
==========
In this section we try to expose the problem we currently have
For example, a scalar subquery can be used as an annotation:

.. code-block:: python

   first_subject = Cohort.objects.order_by("id").values("subject")[:1]

   Sales.objects.annotate(
       first_subject=first_subject
   ).values("first_subject")

The reasons this works:

* ``.values("first_subject")`` is treated like a selected column of
  the ``Sales`` query.
* This happens because Django renders the annotation in the ``SELECT`` clause.
  That is valid for scalar expressions.

But this breaks when we are dealing with multi-column results. For example:

.. code-block:: python
   first_object = Cohort.objects.order_by("id").values("subject", "duration")[:1]

   Sales.objects.annotate(
       first_subject=first_object
   ).values("first_subject__subject", "first_object__duration")

This will raise `Cannot resolve expression type, unknown output_field`. because the ORM does not have an expression representing multiple columns and thus cannot make use of a join against the multi-column subquery.


Set-Returning Functions in ``SELECT``
-------------------------------------

PostgreSQL's ``generate_series()`` is a set-returning function. Today, if it is
used as a scalar annotation, Django renders it in the ``SELECT`` list:

.. code-block:: python

   Sales.objects.annotate(series=GenerateSeriesFunc(1, 3))


Expected SQL:

.. code-block:: sql

   SELECT "SRF_sales"."id", "SRF_sales"."sold_on", "SRF_sales"."day", "series"."value" AS "series"
   FROM "SRF_sales"
   CROSS JOIN LATERAL generate_series(1, 3) AS "series"("value")


The actual SQL generated:

.. code-block:: sql

   SELECT "SRF_sales"."id", "SRF_sales"."sold_on", "SRF_sales"."day", generate_series(1, 3) AS "series"
   FROM "SRF_sales"


The ORM does not expose a way to place the set-returning function in the ``FROM`` clause.


Filtering Set-Returning Annotations
-----------------------------------

Filtering a set-returning annotation also treats the function as a scalar
expression:

.. code-block:: python

   Sales.objects.alias(series=GenerateSeriesFunc(1, 3)).filter(series__gt=1)

Expected SQL:

.. code-block:: sql

   SELECT "SRF_sales"."id", "SRF_sales"."sold_on", "SRF_sales"."day", "series"."value" AS "series"
   FROM "SRF_sales"
   CROSS JOIN LATERAL generate_series(1, 3) AS "series"("value")
   WHERE "series"."value" > 1


The actual SQL generated:

.. code-block:: sql

   SELECT "SRF_sales"."id", "SRF_sales"."sold_on", "SRF_sales"."day", generate_series(1, 3) AS "series"
   FROM "SRF_sales"
   WHERE generate_series(1, 3) > 1

This query fails immediately at the database level. In PostgreSQL, it raises:
``ERROR: set-returning functions are not allowed in WHERE``

This is because the ``WHERE`` clause expects a scalar boolean expression for each row, not a set of rows. The function is duplicated as a set-returning expression in both the ``SELECT`` and ``WHERE`` clauses instead of being treated as a table source.


Comparison: Placing the Function in the ``FROM`` Clause
-------------------------------------------------------

If the set-returning function is instead compiled in the ``FROM`` clause (using a ``LATERAL`` join), the query behavior is clean, valid, and efficient:

.. code-block:: sql

   SELECT "SRF_sales"."id", "SRF_sales"."sold_on", "SRF_sales"."day", "series"."value" AS "series"
   FROM "SRF_sales"
   CROSS JOIN LATERAL generate_series(1, 3) AS "series"("value")
   WHERE "series"."value" > 1

Benefits:

* The function is evaluated as a row source instead of as a scalar expression.
* The ``WHERE`` clause filters a normal column reference such as
  ``"series"."value"``.

Multi-Column Subqueries
-----------------------

Subqueries have a similar limitation. A scalar subquery works when it returns
one column:

.. code-block:: python

   Sales.objects.annotate(
       first_subject=Cohort.objects.order_by("id").values("subject")[:1]
   )

But a queryset returning multiple columns cannot be represented as a scalar:

.. code-block:: python

   Cohort.objects.values("subject", "duration")

As a scalar expression, this has no single ``output_field``. As a table
expression, it could expose named columns:

.. code-block:: python

   Sales.objects.alias(
       cohort_data=Cohort.objects.values("subject", "duration")[:1]
   ).values("cohort_data__subject", "cohort_data__duration")


There are three aspects to this that we'd like to work on:

* A table expression can be registered as a source in ``FROM`` or ``JOIN``.
* A table expression has a stable alias.
* Columns exposed by that alias can be referenced in the rest of the queryset.

Specification
=============

Composite output metadata
-------------------------

The first requirement is a way for an expression or query source to describe
multiple output columns.

For scalar expressions, Django already uses ``Expression.output_field``. For
example, a subquery returning only ``subject`` can expose a single field such as
``CharField``.

For expressions that expose more than one column, Django needs an
equivalent representation for multiple named fields. For example, a subquery or table expression might expose:

.. code-block:: python

   # exposes:
   #   title -> CharField()
   #   body -> TextField()

To solve this, this proposal introduces a ``CompositeField``. This acts as a lightweight composite output field designed
specifically for describing multi-column expression/query output, rather than acting as a concrete database model field.
This distinction matters because the ORM must preserve Django's existing lookup behavior.
By wrapping the output in a ``CompositeField``, if ``posts__title`` resolves to a ``CharField``, then all normal
text lookups and transforms (like ``__icontains``) will automatically continue to work as expected.

Handling multi-column sources
-----------------------------

A multi-column source must describe the columns it exposes:

.. code-block:: python

   subquery = Post.objects.values("title", "body")[:1]
   User.objects.alias(posts=subquery).values("posts__title", "posts__body")

The inner query's selected fields are used to form its ``CompositeField``.

Under this proposal, the source remains in ``Query.annotations`` until one of
its fields, or the complete row, is referenced. Django then checks whether a
``SubqueryJoin`` for that annotation already exists in ``Query.alias_map``. It
reuses the existing join or creates one when needed.

An individual reference such as ``posts__title`` becomes a typed ``Col``
pointing to the derived table. A reference to the complete ``posts`` alias
becomes an internal tuple containing all its columns.

The ORM cannot reliably know whether a query returns one row or many rows. A
caller that requires one row must limit the query, for example with ``[:1]``.

Correlated sources are also part of the intended design:

.. code-block:: python

   subquery = (
       Post.objects.filter(user=OuterRef("pk"))
       .values("title", "body")[:1]
   )
   User.objects.alias(posts=subquery).values("posts__title", "posts__body")

At the SQL level, a correlated source requires ``LATERAL`` or the equivalent
syntax supported by the database.

Expression-like table sources
-----------------------------

After output columns can be represented, the ORM needs a way to identify a
function expression that is valid as a source in the ``FROM`` clause.

A set-returning function can use the same lazy flow as a multi-column queryset:

.. code-block:: python

   Sales.objects.alias(
       series=GenerateSeries(1, 3),
   ).filter(series__gt=1)

The function must describe its output through ``output_field``. A scalar result
can use a normal field, while a multi-column result can use
``CompositeField``.

The exact author-facing opt-in is still open. It may use suitable metadata on a
custom function expression, or a small function base class that authors
inherit.

Table Source Compilation
------------------------

The ORM must also know where and how a table expression should be compiled.

This proposal introduces ``SubqueryJoin`` to represent a multi-column queryset
in the ``FROM`` clause. A function source requires different SQL, so it also
introduces ``SetReturningFunctionJoin``.

Both proposed joins are stored directly in the existing ``Query.alias_map`` and
compiled through the existing ``FROM``-clause machinery. Correlated sources use
``LATERAL`` or the database's equivalent syntax.

This means output metadata alone is not enough. ``output_field`` describes the
columns and their types, while the join describes how the source is compiled.

Query Integration
-----------------

Existing behavior for single-column subqueries does not change. The new logic
is used only when ``filter()``, ``values()``, ``order_by()``, or another
expression references a supported multi-column or set-returning alias.

For example, when the ORM receives:

.. code-block:: python

   .filter(info__email="bob@mail.com")

it splits the name and checks whether ``info`` is present in
``Query.annotations``. If the annotation is a multi-column query, it checks
whether a matching ``SubqueryJoin`` is already present in
``Query.alias_map``. It reuses that join or creates one when needed.

The derived table is then added to the ``FROM`` clause:

.. code-block:: sql

   LEFT OUTER JOIN (
       SELECT email, name
       FROM ...
   ) info ON (1 = 1)

After that, ``info__email`` resolves to a typed ``Col`` pointing to
``info.email``. If the complete annotation is used, it resolves to an internal
tuple containing all its columns.

Set-returning function sources follow the same flow, using their
function-specific join representation.

The source is added only when it is needed, and multiple references reuse the
same join. The existing filtering, selection, annotation, and ordering
machinery continues from the resulting ``Col`` or tuple.

Rationale
=========

Why ``output_field`` Matters
----------------------------

In Django, most expressions expose their internal data types and lookup capabilities through the ``output_field``. This architecture works naturally for standard scalar expressions that return a single column.

However, queries that expose multiple columns need a similar mechanism to expose their underlying schema. Rather than proposing a completely new API interface to handle multi-column results, this design leans heavily into the existing ``output_field`` pattern.

By proposing that multi-column expressions dynamically generate a ``CompositeField`` and assign it to their ``output_field``, these queries will seamlessly satisfy Django's internal ``BaseExpression`` interface. This approach allows the ORM to resolve multi-column lookups (e.g., ``posts__title``) using the exact same code paths it already uses for standard scalar transformations, drastically reducing the required complexity of the implementation.


Why ``alias()`` Is a Candidate API
----------------------------------

``QuerySet.alias()`` already lets users give temporary names to expressions
inside a query.

Table expression aliases are similar from the user's point of view:

.. code-block:: python

   Sales.objects.alias(series=GenerateSeries(1, 3))

The alias remains lazy until another queryset operation references it. This
fits multi-column querysets and set-returning functions without requiring a
new wrapper around every source.

Why reuse the multi-column subquery path?
-----------------------------------------

Multi-column querysets and set-returning functions need the same operation:
turn a lazy annotation into a ``FROM`` source and resolve its output into
typed ``Col`` expressions.

The proposed design uses ``Query.annotations``, ``Query.alias_map``, alias
allocation, and ``SubqueryJoin``. A function source can reuse that flow and add
only the join behavior required for its SQL syntax.

Alternatives Considered
=======================

A generic ``TableExpression`` wrapper
-------------------------------------

An earlier approach wrapped a source explicitly:

.. code-block:: python

   User.objects.alias(posts=TableExpression(subquery))

This is explicit, but it adds another public abstraction and encourages a
separate resolution layer. The initial cases can use the annotation and join
machinery directly. A generic wrapper can be reconsidered if more kinds of
arbitrary ``FROM`` sources are added later.

A small function base class
---------------------------

One possible function opt-in is a small ``Func`` subclass, provisionally
called ``TableFunction``:

.. code-block:: python

   class GenerateSeries(TableFunction):
       function = "generate_series"
       output_field = IntegerField()

Function authors could inherit it when defining their own set-returning
functions. This is one possible API, not a required part of this DEP. Another
option is suitable metadata on a top-level custom ``Func`` used through
``alias()``.

The final choice must preserve existing ``SELECT``-list behavior and distinguish
an expression that returns multiple rows from one that is valid as a complete
``FROM`` source.

Explicit Column Metadata
------------------------

An early implementation could accept column metadata directly:

.. code-block:: python

   JsonEach(
       "payload",
       columns={
           "key": models.TextField(),
           "value": models.JSONField(),
       },
   )

This may be easy to prototype, but it creates a separate metadata path from
``Expression.output_field``.

You can find more detail `here <https://github.com/p-r-a-v-i-n/Generic---Relation---API-Design/blob/main/RELATION_API_BLUEPRINT.md>`_.

Backwards Compatibility
=======================

Existing single-column subqueries and ordinary scalar expressions keep their
current behavior.

Only an explicitly supported function alias becomes a table source. Merely
setting ``set_returning`` or returning more than one row must not silently
change where an existing expression is compiled until the final opt-in
contract is agreed.

The proposal does not introduce concrete model fields, migrations, or database
schema changes.

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license
(http://creativecommons.org/publicdomain/zero/1.0/deed).
