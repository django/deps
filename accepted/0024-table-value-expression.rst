DEP 0024: Support for Table Expressions in the Django ORM
=======================================================

:DEP: 0024
:Author: Pravin Kamble
:Implementation Team: Pravin Kamble
:Shepherd: Jacob Walls
:Status: Accepted
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

The proposal defines the intended public behavior. Function expressions
explicitly opt in when they are valid as table sources. Private class names
and implementation details may continue to evolve.

Motivation
==========

Some database expressions produce a set of rows or expose multiple columns
instead of returning one scalar value. Application developers should be able
to use these expressions as query sources and work with their columns through
the normal queryset API.

This proposal provides three related capabilities:

* A table expression can be added as a source in ``FROM`` or ``JOIN``.
* The source has a stable alias.
* Columns exposed by that alias can be selected, filtered, ordered, and used in
  other expressions.

Placing these expressions in the ``FROM`` clause allows the database to treat
them as row sources rather than scalar values. Their output columns can then be
referenced normally from ``SELECT``, ``WHERE``, and other query clauses. For
example, filtering a set-returning function should produce SQL in this form:

.. code-block:: sql

   SELECT "SRF_sales"."id", "SRF_sales"."sold_on", "SRF_sales"."day"
   FROM "SRF_sales"
   CROSS JOIN LATERAL generate_series(1, 3) AS "series"("series")
   WHERE "series"."series" > 1

Here, the function is evaluated as a row source and ``WHERE`` filters a normal
column reference.

Multi-Column Subqueries
-----------------------

A scalar subquery can be used as an annotation:

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

   first_object = Cohort.objects.order_by("id").values(
       "subject", "duration"
   )[:1]

   Sales.objects.annotate(
       first_object=first_object,
   ).values("first_object__subject", "first_object__duration")

This raises ``Cannot resolve expression type, unknown output_field`` because
the ORM does not have an expression representing multiple columns and thus
cannot make use of a join against the multi-column subquery.

As a table source, the same queryset could expose named columns:

.. code-block:: python

   Sales.objects.alias(
       first_object=first_object,
   ).values("first_object__subject", "first_object__duration")

The single-column restriction has also led to third-party workarounds.
Baptiste Mispelon's `article on returning a model instance from a subquery
<https://blog.bmispelon.rocks/articles/2024/2024-05-09-django-getting-a-full-model-instance-from-a-subquery.html>`_
describes combining several model fields into one JSON value and converting
that value back into a model instance. The technique is also available in the
`django-model-subquery package
<https://github.com/bmispelon/django-model-subquery>`_.

This proposal takes a different approach: the subquery remains a table source
whose columns keep their individual field types and can be referenced through
its alias.


Set-Returning Functions in ``SELECT``
-------------------------------------

PostgreSQL's ``generate_series()`` is a set-returning function. Today, if it is
used as a scalar annotation, Django renders it in the ``SELECT`` list:

.. code-block:: python

   Sales.objects.annotate(series=GenerateSeriesFunc(1, 3))


Expected SQL:

.. code-block:: sql

   SELECT "SRF_sales"."id", "SRF_sales"."sold_on", "SRF_sales"."day", "series"."series" AS "series"
   FROM "SRF_sales"
   CROSS JOIN LATERAL generate_series(1, 3) AS "series"("series")


The actual SQL generated:

.. code-block:: sql

   SELECT "SRF_sales"."id", "SRF_sales"."sold_on", "SRF_sales"."day", generate_series(1, 3) AS "series"
   FROM "SRF_sales"


The ORM does not expose a way to place the set-returning function in the
``FROM`` clause.


Filtering Set-Returning Annotations
-----------------------------------

Filtering a set-returning annotation also treats the function as a scalar
expression:

.. code-block:: python

   Sales.objects.alias(series=GenerateSeriesFunc(1, 3)).filter(series__gt=1)

The actual SQL generated:

.. code-block:: sql

   SELECT "SRF_sales"."id", "SRF_sales"."sold_on", "SRF_sales"."day"
   FROM "SRF_sales"
   WHERE generate_series(1, 3) > 1

This query fails immediately at the database level. In PostgreSQL, it raises:
``ERROR: set-returning functions are not allowed in WHERE``

This is because the comparison in ``WHERE`` expects one scalar value for each
row, not a set of rows. The function is compiled directly in ``WHERE`` instead
of being treated as a table source. The intended ``FROM`` form is shown at the
beginning of this section.

Specification
=============

Composite output metadata
-------------------------

The first requirement is a way for an expression or query source to describe
multiple output columns.

For scalar expressions, Django already uses ``Expression.output_field``. For
example, a subquery returning only ``subject`` can expose a single field such as
``CharField``.

For expressions that expose more than one column, Django needs an equivalent
representation for multiple named fields. For example, a subquery or table
source might expose:

.. code-block:: python

   # exposes:
   #   title -> CharField()
   #   body -> TextField()

To solve this, this proposal introduces a ``CompositeField``. This acts as a
lightweight composite output field designed specifically for describing
multi-column expression or query output, rather than as a concrete database
model field.

By wrapping the output in a ``CompositeField``, if ``posts__title`` resolves
to a ``CharField``, then normal text lookups and transforms such as
``__icontains`` continue to work.

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

A source with multiple columns cannot be selected as one annotation because
there is no single result column for Django to place in ``SELECT``. This
restriction applies even if a later ``values()`` call asks for only one of its
components:

.. code-block:: python

   # Not supported.
   User.objects.annotate(
       posts=Post.objects.values("title", "body")[:1],
   ).values("posts__title")

The source must instead be registered with ``alias()`` and its columns selected
individually:

.. code-block:: python

   User.objects.alias(
       posts=Post.objects.values("title", "body")[:1],
   ).values("posts__title")

The complete alias may still resolve internally to a tuple when an operation,
such as a tuple lookup, needs all of its columns. That internal tuple does not
make the source selectable as one annotation.

The ORM cannot reliably know whether a query returns one row or many rows. A
caller that requires one row must limit the query, for example with ``[:1]``.

Correlated multi-column sources require ``LATERAL`` support. PostgreSQL,
MySQL 8.0.14+, and Oracle support ``LATERAL``. MariaDB and SQLite do not:

.. code-block:: python

   subquery = (
       Post.objects.filter(user=OuterRef("pk"))
       .values("title", "body")[:1]
   )
   User.objects.alias(posts=subquery).values("posts__title", "posts__body")

Expression-like table sources
-----------------------------

After output columns can be represented, the ORM needs a way to identify a
function expression that is valid as a source in the ``FROM`` clause.

A set-returning function can use the same lazy flow as a multi-column queryset:

.. code-block:: python

   class GenerateSeries(Func):
       function = "generate_series"
       output_field = IntegerField()
       table_source = True


   Sales.objects.alias(
       series=GenerateSeries(1, 3),
   ).filter(series__gt=1)

The ``table_source`` attribute is the explicit opt-in: it says that the
function expression is valid as a complete source in the ``FROM`` clause.
It is intentionally separate from the existing ``set_returning`` attribute.
``set_returning`` keeps its existing meaning that an expression may produce
more than one row; by itself, it does not move the expression into ``FROM``.
A function may set both attributes, but they are not interchangeable.

The function must describe its output through ``output_field``. A
single-column source can use a normal field, while a multi-column source uses
``CompositeField``:

.. code-block:: python

   class JsonEach(Func):
       function = "json_each"
       output_field = CompositeField(
           key=TextField(db_column="key"),
           value=JSONField(db_column="value"),
       )
       table_source = True


   Data.objects.alias(item=JsonEach("payload")).values(
       "item__key",
       "item__value",
   )

The names in ``CompositeField`` are the names referenced by the queryset.
``db_column`` can map each name to the column exposed by the database
function. For a single-column source, ``db_column`` can provide the same
mapping. If it is omitted, the table-source alias or composite field name is
used.

As with multi-column querysets, a multi-column function source is registered
with ``alias()`` and its columns are selected individually. Selecting the
complete source through ``annotate()`` is not supported. A single-column table
source may still be selected with ``annotate()``.

Table Source Compilation
------------------------

The ORM must also know where and how a table expression should be compiled.

This proposal introduces ``SubqueryJoin`` to represent a multi-column queryset
in the ``FROM`` clause. A function source requires different SQL, so it also
introduces ``SetReturningFunctionJoin``.

Both proposed joins are stored directly in the existing ``Query.alias_map`` and
compiled through the existing ``FROM``-clause machinery. A function source can
use ``LATERAL`` when required by the backend. Correlated sources use the syntax
required by each database.

``output_field`` lets the ORM resolve the names and types of columns exposed by
a table source, but it doesn't describe how to add that source to the SQL
``FROM`` clause. A multi-column queryset must be compiled as a derived table.
The join representation provides this compilation behavior.

The infrastructure is database-independent, but table-valued functions are
not. Function names, argument syntax, exposed column names, and whether a
column definition clause is required vary by database. Custom ``Func``
expressions remain responsible for vendor-specific SQL through methods such as
``as_postgresql()``, ``as_mysql()``, or ``as_oracle()``.

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

   CROSS JOIN (
       SELECT email, name
       FROM ...
   ) info

This query can match ``email`` even when ``info`` is empty:

.. code-block:: python

   .filter(Q(email="bob@mail.com") | Q(info__email="bob@mail.com"))

This uses a ``LEFT OUTER JOIN``:

.. code-block:: sql

   LEFT OUTER JOIN (...) info ON (1 = 1)

After that, ``info__email`` resolves to a typed ``Col`` pointing to
``info.email``. If an operation needs the complete alias, it can resolve to an
internal tuple containing all its columns. A multi-column source cannot be
selected as one annotation.

Set-returning function sources follow the same flow, using their
function-specific join representation.

The source is added only when it is needed, and multiple references reuse the
same join. The existing filtering, selection, annotation, and ordering
machinery continues from the resulting ``Col`` or tuple.

Join type follows normal queryset boolean semantics. When a table source is
required by the query, it is compiled as a ``CROSS`` join. For example, assume
that ``Sales`` contains an object with primary key 1 for Monday and another
with primary key 2 for Tuesday:

.. code-block:: python

   sales = (
       Sales.objects.annotate(series=GenerateSeries(1, 3))
       .filter(series__gt=1)
       .order_by("pk", "series")
   )

   [(sale.pk, sale.series) for sale in sales]
   # [(1, 2), (1, 3), (2, 2), (2, 3)]

The function initially produces the values 1, 2, and 3 for each ``Sales``
object. The filter removes ``(1, 1)`` and ``(2, 1)``, leaving the two values
shown above for each object. If the function returns no rows, the corresponding
``Sales`` object also produces no result.

When a table source is referenced only by one side of an ``OR`` condition, it
must not remove a base row that satisfies the other side. In that case it is
compiled as a ``LEFT OUTER`` join:

.. code-block:: python

   Sales.objects.alias(
       series=GenerateSeries(1, 3),
   ).filter(Q(day="Monday") | Q(series__gt=1))

Selecting a column from the source makes the source required, even when a
filter would otherwise make it optional. Changing only ``alias()`` to
``annotate()`` selects ``series``:

.. code-block:: python

   sales = (
       Sales.objects.annotate(
           series=GenerateSeries(1, 3),
       )
       .filter(Q(day="Monday") | Q(series__gt=1))
       .order_by("pk", "series")
   )

   [(sale.pk, sale.series) for sale in sales]
   # [(1, 1), (1, 2), (1, 3), (2, 2), (2, 3)]

Every returned object now needs a value for ``series``, so the table source is
required and uses a ``CROSS`` join. If the function returns no rows, there is
no ``series`` value to select and the corresponding ``Sales`` object produces
no result.

Rationale
=========

Why ``output_field`` Matters
----------------------------

In Django, most expressions expose their internal data types and lookup
capabilities through ``output_field``. This architecture works naturally for
standard scalar expressions that return a single column.

However, queries that expose multiple columns need a similar mechanism for
their schema. Rather than proposing a completely new API for multi-column
results, this design uses the existing ``output_field`` pattern.

By assigning a generated ``CompositeField`` to ``output_field``, a
multi-column expression satisfies Django's existing ``BaseExpression``
interface. The ORM can then resolve a reference such as ``posts__title``
through the same typed lookup and transform machinery used for scalar fields.


Why ``alias()`` Is Used
-----------------------

``QuerySet.alias()`` already lets users give temporary names to expressions
inside a query.

Table expression aliases are similar from the user's point of view:

.. code-block:: python

   Sales.objects.alias(series=GenerateSeries(1, 3))

The alias remains lazy: Django adds the source to the ``FROM`` clause only when
a later queryset operation references it. For example, merely declaring
``series=GenerateSeries(1, 3)`` doesn't repeat every ``Sales`` row three times.

Why reuse the multi-column subquery path?
-----------------------------------------

Multi-column querysets and set-returning functions need the same operation:
turn a lazy annotation into a ``FROM`` source and resolve its output into
typed ``Col`` expressions.

Using the same resolution path gives both kinds of source consistent queryset
behavior. Their aliases remain lazy, their output columns support normal field
lookups and transforms, and boolean conditions determine whether the source is
required or optional. Only the SQL used to render each source is different.

Alternatives Considered
=======================

A generic ``TableExpression`` wrapper
-------------------------------------

An earlier approach wrapped a source explicitly:

.. code-block:: python

   User.objects.alias(posts=TableExpression(subquery))

This is explicit, but it adds another public abstraction and encourages a
separate resolution layer. The proposed cases can use the annotation and join
machinery directly. A generic wrapper can be reconsidered if more kinds of
arbitrary ``FROM`` sources are added later.

A convenience ``Func`` subclass could be added later for projects defining
many table-valued functions. It is not required by this proposal because a
custom ``Func`` can opt in directly with ``table_source = True``.

Explicit Column Metadata
------------------------

Another rejected implementation idea could have accepted column metadata directly:

.. code-block:: python

   JsonEach(
       "payload",
       columns={
           "key": models.TextField(),
           "value": models.JSONField(),
       },
   )

This is explicit, but it creates a separate metadata path from
``Expression.output_field``.


Backwards Compatibility
=======================

Existing single-column subqueries and ordinary scalar expressions keep their
current behavior.

Only an expression with ``table_source = True`` becomes a table source. Merely
setting ``set_returning`` or returning more than one row does not change where
an existing expression is compiled. Existing expression classes remain
unchanged unless they explicitly adopt the new attribute.

Selecting a multi-column source as one annotation remains unsupported. Users
register it with ``alias()`` and select its component columns instead.

The proposal does not introduce concrete model fields, migrations, or database
schema changes.

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license
(http://creativecommons.org/publicdomain/zero/1.0/deed).
