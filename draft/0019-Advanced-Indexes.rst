==========================
DEP 0019: Advanced Indexes
==========================

:DEP: 0019
:Author: Marc Tamlyn, Akshesh Doshi
:Status: Draft
:Type: Feature
:Created: 2016-03-03

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========
This proposal aims to bring flexibility in Django on what it can do with db
indexes and allow Django to support more complex indexes on relevant backends
(most notably PostgreSQL), such as functional indexes and indexes with different
algorithms (e.g. ``GiST``).

Motivation
==========

There are new fields being introduced in ``contrib.postgres`` which have
similar issues to the rationale for ``spatial_index``, a ``BTree`` index is
either insufficent, inefficient or does not work and an alternative index type
is needed for that field. A field should be able to declare the type of index which
is appropriate to it.

Also indexes need to be made more customisable, like to be able to extend
support for `DEFERRABLE INITIALLY DEFERRED for UNIQUE constraints
<https://code.djangoproject.com/ticket/20581>`_.

In addition, both postgres and oracle support powerful functional indexes
(and mysql supports indexing on the first few characters of a string), which
allow significant performance benefits for certain queries. Of course, it is
possible to create these indexes by hand if you know what you are doing using
``RunSQL`` based migrations but this is a place for improvement.

PostgreSQL also supports partial indexes.

With the recent advances in expression syntax, they can be extended to indexes
with modifications in the way indexes work.

Proposed solution and specifications
====================================

Introduce ``django.db.models.indexes`` with deconstructable ``Index`` class.
This will be inherited by different index algorithms such as ``BTree`` and ``Hash``,
and also ``FunctionalIndex(expression)``.

``Index`` classes will take 3 optional arguments ``fields``, ``model`` and ``name``.
Both name of the field ``"slug"`` or the field object itself (``self.slug``) will be
allowed to be passed as arguments to ``fields``.

``Index()`` classes will be able to define their own SQL using the ``as_sql``
pattern similar to that used by ``Lookup()``, but will be passed to the
``SchemaEditor`` class instead of a compiler. By default, this will defer to
the ``SchemaEditor`` class, but it allows non-standard index creation such as
that for spatialite (using a ``SELECT`` statement and a function) without
having to subclass ``SchemaEditor``.

Introduce ``Meta.indexes`` for other indexes. This will contain a list of
``Index()`` instances. ``index_together`` will continue to be supported but
will be translated into ``Meta.indexes`` internally and handled only there by
``SchemaEditor``.

The general workflow for index addition/deletion would be -
migrations framework detects that Meta.indexes has changed => models layer
tells migrations that due to the change a new index needs to be added/deleted
=> migrations framework implements this change.

In order to have a robust way to detect name changes in indexes, the entire
index name will be explicitly passed from the operation to migrations, whether
they are auto-generated or not.

``db_index`` of the ``Field`` class will support index classes
(e.g. ``IntegerField(db_index=indexes.Hash)``) other than the values
``True`` and ``False``. Passing an index not supported by the user's
backend to this argument would raise a ``NotImplementedError``.

``Field`` will gain a method ``get_default_index`` which will be called when
``db_index=True`` is passed to the ``__init__``. The default value would be
the ``SpatialIndex`` in gis, which will mark the start of deprecation of
``spatial_index`` which would be supported with deprecation warnings.

``db_index``, ``index_together`` would actually become shortcuts for
editing ``Meta.indexes``. Also a new attribute ``index_type`` can be added
to ``Field`` which can be used to use an index other than the default index
for that field and would be ignored if ``db_index`` is ``False``, if that level
of customisability is required.

``Index()`` subclasses will also have a ``supports(backend)`` method which
returns ``True`` or ``False`` depending on whether the backend supports that
index type.

Example::

    class Town(models.Model):
        name = models.CharField(max_length=255)
        slug = models.SlugField(unique=True)
        region = gis.PolygonField(db_index=True)
        area = models.FloatField()
        population_density = models.FloatField()

        class Meta:
            indexes = [
                models.BTree(fields=['slug', self.name]),
                models.FunctionalIndex(expression=(F('area') * F('population_density')),
                    type=models.BTree),
            ]

Backwards compatibility
=======================

``spatial_index`` will be deprecated as setting ``db_index`` on a spatial field
will be sufficient.

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).
