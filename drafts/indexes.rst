Advanced indexes
================

:Created: 2014-09-14
:Author: Marc Tamlyn
:Status: Draft

Abstract
========

This DEP aims to rework how Django handles index definitions. This will allow
Django to support more complex indexes on the relevant backends (most notably
PostgreSQL), such as functional indexes and indexes with different algorithms
(e.g. ``GiST``).

Current Implementation
======================

At present, Django has several APIs for creating indexes, some of which are
implicit: ``primary_key``, ``db_index`` and ``unique`` on a ``Field()``,
``unqiue_together`` and ``index_together`` in ``class Meta``, and
``spatial_index`` on a ``Field()`` in GIS.

There is additional complexity in that handling of these APIs is done in both
``DatabaseCreation`` and in ``SchemaEditor`` at present. Given that
``DatabaseCreation`` is deprecated, and set to be removed in Django 2.0, we
will only consider how ``SchemaEditor`` handles indexes for now.

For the ``primary_key`` and ``unique`` on fields it is not necessary to create
indexes by hand on any of the supported backends as the database handles these
itself.

``unique`` and ``unique_together`` are handled by using the SQL ``CONSTRAINT``
rather than ``INDEX``, or by using the ``UNIQUE`` keyword when creating the
column or table at the same time.

So that leaves ``db_index`` and ``index_together`` which use a shared API on
``SchemaEditor``, encapsulated in the ``_create_index_sql`` statement.

``spatial_index`` in gis duplicates similar code in customised ``SchemaEditor``
subclasses for the Postgis backend, and uses somewhat different syntax for the
sqlite backend. As far as I can tell ``spatial_index`` is currently not handled
by any ``SchemaEditor`` for MySQL or Oracle, despite the old
``DatabaseCreation`` classes handling it correctly (and very similarly to
Postgis.

Motivation
==========

There are new fields being introduced in ``contrib.postgres`` which have
similar issues to the rationale for ``spatial_index`` - a ``BTree`` index is
either insufficent, inefficient or does not work and an alternative index type
is needed for that field. A field should be able to declare the type of index
which is appropriate to it.

In addition, both postgres and oracle support powerful functional indexes (and
mysql support indexing on the first few characters of a string), which allow
significant performance benefits for certain queries. Of course, it is possible
to create these indexes by hand if you know what you are doing using ``RunSQL``
based migrations.

PostgreSQL also support partial indexes.

Specification
=============

Introduce ``django.db.models.indexes`` with deconstructable ``Index`` classes.
These will include different index algorithms such as ``BTree`` and ``Hash``,
and also ``FunctionalIndex(expression)``.

``Index()`` classes will be able to define their own SQL using the ``as_sql``
pattern similar to that used by ``Lookup()``, but being passed the
``SchemaEditor`` class instead of a compiler. By default, this will defer to
the ``SchemaEditor`` class, but it allows non-standard index creation such as
that for spatialite (using a ``SELECT`` statement and a function) without
having to subclass ``SchemaEditor``.

``Index()`` subclasses will also have a ``supports(backend)`` method which
returns ``True`` or ``False`` depending on whether the backend supports that
index type.

``Field(db_index=)`` will support either the value ``True``, or an index class
(e.g. ``IntegerField(db_index=indexes.Hash)``).

``Field`` will gain a method ``get_default_index`` which will be called when
``db_index=True`` is passed to the ``__init__``. This will be used in place of
``spatial_index`` in gis, which will be supported with deprecation warnings.

Introduce ``Meta.indexes`` for other indexes. This will contain a list of
``Index()`` instances. ``index_together`` will continue to be supported but
will be inserted into ``Meta.indexes`` and handled only there by
``SchemaEditor``.

Example::

    class River(models.Model):
        name = models.CharField(max_length=255)
        slug = models.SlugField(unique=True)
        route = gis.LineStringField(db_index=True)
        length = models.FloatField()
        average_capacity = models.FloatField()

        class Meta:
            indexes = [
                models.BTree(fields=['slug', 'name']),
                models.FunctionalIndex(expression=(F('length') * F('average_capacity')),
                    type=models.BTree),
            ]

Backwards compatibility
=======================

``spatial_index`` will be deprecated as setting ``db_index`` on a spatial field
will be sufficient.

The main concern is whether to fully support the new API on
``DatabaseCreation`` as well as in ``SchemaEditor``.
