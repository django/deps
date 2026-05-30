DEP XXXX: Table Expressions in the Django ORM
=============================================

:DEP: XXXX
:Author: Pravin Kamble
:Implementation Team: Jacob Walls and Pravin Kamble
:Shepherd: -
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
       first_subject=Subquery(first_subject)
   ).values("first_subject")

The reasons this works.
1. Here the result of alias `first_object` will be treated as same columns of Sales table.
2. The reason why it treat as same column as other columns of Sales table is bcs here django uses `SELECT` clause. and this is fair.

But this breaks when we are dealing with multi-columns results. for example:
```python
   first_object = Cohort.objects.order_by("id").values("subject", "duration")[:1]

   Sales.objects.annotate(
       first_subject=Subquery(first_object)
   ).values("first_subject")
```
This will raise `Cannot resolve expression type, unknown output_field`. bcs ORM don't know how to handle the multi-columns.


Set-Returning Functions in ``SELECT``
-------------------------------------

PostgreSQL's ``generate_series()`` is a set-returning function. Today, if it is
used as an annotation, Django renders it in the ``SELECT`` list:

.. code-block:: python

   Sales.objects.annotate(
       series=GenerateSeries(1, 3)
   ).values("series")

Conceptual SQL shape today:

.. code-block:: sql

   SELECT generate_series(1, 3) AS "series"
   FROM "sales"

This treats ``generate_series()`` like a scalar expression selected from the
base table.


Filtering Set-Returning Annotations
-----------------------------------

Filtering a set-returning annotation also treats the function as a scalar
expression:

.. code-block:: python

   Sales.objects.annotate(
       series=GenerateSeries(1, 3)
   ).filter(series__gt=1)

Conceptual SQL shape today:

.. code-block:: sql

   SELECT ..., generate_series(1, 3) AS "series"
   FROM "sales"
   WHERE generate_series(1, 3) > 1

The function is still not a table source. It is duplicated as an expression in
the ``SELECT`` and ``WHERE`` clauses.

Multi-Column Subqueries
-----------------------

Subqueries have a similar limitation. A scalar subquery works when it returns
one column:

.. code-block:: python

   Sales.objects.annotate(
       first_subject=Subquery(
           Cohort.objects.order_by("id").values("subject")[:1]
       )
   )

But a queryset returning multiple columns cannot be represented as a scalar
``Subquery``:

.. code-block:: python

   Cohort.objects.values("subject", "duration")

As a scalar expression, this has no single ``output_field``. As a table
expression, it could expose named columns:

.. code-block:: python

   Sales.objects.alias(
       cohort_data=TableExpression(
           Cohort.objects.values("subject", "duration")
       )
   ).values("cohort_data__subject", "cohort_data__duration")


There are three aspects to this that we'd like to work on:
- A table expression can be registered as a source in ``FROM`` or ``JOIN``.
- A table expression has a stable alias.
- Columns exposed by that alias can be referenced in the rest of the queryset.

Specification
=============


This DEP uses ``TableExpression`` as a placeholder name. The final public API
may use a different name.

Example:

.. code-block:: python

   Sales.objects.alias(
       series=TableExpression(GenerateSeries(1, 3))
   ).filter(series__value__gt=1)

For single-column table expressions, the final API may allow a shorter form such
as ``series__gt=1``. That detail is still open.

Handling multi-columns
----------------------

A table expression must describe the columns it exposes.

For a single-column source:

.. code-block:: python

   GenerateSeries(1, 3)
   # exposes: value -> IntegerField()

For a multi-column source:

.. code-block:: python

   JsonEach("payload")
   # exposes:
   #   key -> TextField()
   #   value -> JSONField()

The implementation should preserve Django's existing lookup behavior by
associating each exposed column with a Django field.

The exact mechanism is open. One possible direction is to represent
multi-column output through ``Expression.output_field`` using a composite output
representation.

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

Why Focus on the Problem Before a Specific Class
------------------------------------------------

The first question is the ORM capability Django needs:

* represent table-like query sources,
* know their output columns,
* and resolve references to those columns.

Once that capability is clear, the exact internal object model can be evaluated.

Why ``output_field`` Matters
----------------------------

Most Django expressions expose their result type through ``output_field``.
This works naturally for scalar expressions.

Table expressions need something similar, but they may expose multiple columns.
Using an ``output_field``-based design may allow table-like expressions to fit
the existing ``Expression`` interface more naturally.


Why ``alias()`` Is a Candidate API
----------------------------------

``QuerySet.alias()`` already lets users give temporary names to expressions
inside a query.

Table expression aliases are similar from the user's point of view:

.. code-block:: python

   Sales.objects.alias(
       item=TableExpression(JsonEach("payload"))
   )

Internally, however, table expression aliases are different from scalar
annotation aliases. They must be registered as table sources, not only as
reusable scalar expressions.

Alternatives Considered
=======================

Composite Output Metadata
-------------------------

Another approach is to represent the output shape through ``output_field``:

.. code-block:: python

   class JsonEach(Func):
       function = "json_each"
       output_field = CompositetField([
           ("key", models.TextField()),
           ("value", models.JSONField()),
       ])

This may integrate better with the rest of the ORM, but it requires more
exploration of Django's field and expression internals.

Relation-Style API
------------------

One possible design is a dedicated relation wrapper:

.. code-block:: python

   Sales.objects.alias(
       item=Relation(JsonEach("payload"))
   )

That design may require helper objects to bridge relation aliases to column
references.


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


Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license
(http://creativecommons.org/publicdomain/zero/1.0/deed).

