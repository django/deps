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
* Join and Cardinality Control: Compiling the function in the ``FROM`` clause allows the ORM to choose between ``LEFT JOIN LATERAL`` (preserving the parent rows when the set is empty) and ``CROSS JOIN LATERAL``.
* Valid Filtering: The ``WHERE`` clause filters on the materialized column reference ``"series"."value"`` instead of executing a set-returning function inline. This evaluates correctly and I assume no database execution errors.

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
- A table expression can be registered as a source in ``FROM`` or ``JOIN``.
- A table expression has a stable alias.
- Columns exposed by that alias can be referenced in the rest of the queryset.

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

Handling multi-columns single row
---------------------------------

A table expression must describe the columns it exposes.

For a multi-column source:

.. code-block:: python

   subquery = Post.objects.filter(user=OuterRef("pk")).values("title", "body")[:1]
   User.objects.alias(posts=subquery).values("posts__title", "posts__body")

On the fly we will set the ``output_field`` of the subquery to CompositeField.
This could be achieved when the initial ``resolve_ref()`` is triggered to get the transform.
When Django tries to extract the subfield, it delegates to ``BaseExpression.get_transform()`` which looks up ``self.output_field``.

This seamlessly triggers ``sql/Query.output_field`` on the inner query, which is exactly where we can evaluate
the query's select list and dynamically form the ``CompositeField`` to handle the extraction.

Expression-like table sources
-----------------------------
After output columns can be represented, the ORM needs a way to explicitly register an expression or query as a table source in the ``FROM`` clause.
We can be sure if subqueries return multi-column single row or multi-column multi-row. For example:
.. code-block:: python
   subquery = Post.objects.filter(user=first_user).values("title", "body")
   User.objects.alias(posts=subquery).values("posts__title", "posts__body")
In this example, the ORM cannot reliably know if the ``subquery`` returns exactly one row or multiple rows.
To solve this, our approach requires the developer to explicitly declare when a result is a multi-row table source. The user will do this by wrapping the queryset in a ``TableExpression``.
.. code-block:: python
   User.objects.alias(posts=TableExpression(subquery))
This explicit wrapper allows the ORM to cleanly separate the processing logic. When encountering a ``TableExpression``, the ORM knows to place the subquery inside the ``FROM`` clause (utilizing ``LATERAL`` joins if there are outer references) rather than resolving it as a scalar subquery in the ``SELECT`` clause.
*(Note: This DEP uses ``TableExpression`` as a placeholder name. The final public API may use a different name).*

Table Source Compilation
------------------------

The ORM must also know where and how a table expression should be compiled.

Examples include:

* inline in the ``FROM`` clause,
* as a ``LATERAL JOIN``,
* or, in future work, as a ``WITH``/CTE binding.

This means output metadata alone is not enough. The ORM also needs table-source
compilation behavior.

Query Integration
-----------------

Table expression aliases should be usable in common queryset operations:

.. code-block:: python

   .values("item__key")
   .filter(item__key="name")
   .order_by("item__key")
   .annotate(key_copy=F("item__key"))

The exact resolver integration point is open. Candidate locations include
``Query.resolve_ref()``, ``Query.setup_joins()``, ``Query.names_to_path()``, or
a smaller helper shared by multiple query paths.

Rationale
=========

Why ``FilteredRelation`` is relevant
------------------------------------
It's the only way users have today to insert content into the ``JOIN`` clause (by appending a condition to the ``ON`` clause).


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

In the below example we are assuming expression returns multi-row resuls. Thus wrapped by ``TableExpression``.
.. code-block:: python

   Sales.objects.alias(
       item=TableExpression(JsonEach("payload"))
   )

Internally, however, table expression aliases are different from scalar
annotation aliases. They must be registered as table sources, not only as
reusable scalar expressions.

Alternatives Considered
=======================

Explicit Column Metadata
------------------------

An early implementation could accept column metadata directly:

.. code-block:: python

   TableExpression(
       JsonEach("payload"),
       columns={
           "key": models.TextField(),
           "value": models.JSONField(),
       },
   )

This may be easy to prototype, but it creates a separate metadata path from
``Expression.output_field``.

You can find more detail `here <https://github.com/p-r-a-v-i-n/Generic---Relation---API-Design/blob/main/RELATION_API_BLUEPRINT.md>`_.

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license
(http://creativecommons.org/publicdomain/zero/1.0/deed).
