=========================
DEP 191: Composite Fields
=========================

:DEP: 191
:Author: Thomas Stephenson
:Implementation Team: Thomas Stephenson
:Shepherd: __
:Status: Draft
:Type: Feature
:Created: 2015-03-12
:Last-Modified: 2015-03-12

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

Define a new type of virtual field which maps onto one or more concrete
database fields in the model's table. These fields can be used to define
table constraints which span multiple columns with greater locality than if the
same constraints were created using the current ``index_togther`` or
``unique_together`` APIs.

Specification
=============

CompositeField
--------------

A ``CompositeField`` is a new virtual field type which combines multiple columns
on a model's table into a single object, which is accessible from model
instances.

The value of a ``CompositeField`` on a model instance is either, depending on

* A ``dict``, mapping subfield values to their values on the model (the
  default); or
* A ``tuple`` of the field's subfield values, ordered with the default subfield
  ordering.

depending on the value of ``field.value_is_tuple``.

Limiting the field to either dicts or tuples seems restrictive, but supporting
arbitrary python objects is proposed as part of DEP 192.

Subfield
--------

A ``subfield`` of a composite field is a delegate for another field on the same
model. The value for a subfield on a model instance is the same as the value
for the proxied field.

Subfields are ordered firstly by the execution order of calling the ``__init__``
method of the composite field, and then within the composite field by the
execution order of the proxied field.


Descriptor
----------

Since a composite field does not directly store a value on the model instance,
a python descriptor which delegates getting/setting the instance value of the
subfields is available from


Providing a constraint that spans multiple columns
--------------------------------------------------

A new top-level function will be added to the models API with the following
signature

.. code:: Python

    def constrain(*fields, unique=False, index=True, value_is_tuple=False)

The ``constrain`` function will create a `CompositeField` in the model and add
subfields to the composite field in the order in which they appear in the
argument list.

.. code:: python

    class MyModel(models.Model):
        x = models.IntegerField()
        y = models.IntegerField()

        point = models.constrain(x, y, unique=True, value_is_tuple=True)

This code inserts a composite field, with the name ``point`` to the model. A
constraint which ensures the uniqueness of the point will be added to the table
and an index will be added to support improved lookups on the ``point`` object.


*Note*: In this initial implementation, only ``UNIQUE`` constraints and ``INDEX``
statements are supported. However the same technique should be available to
create ``CHECK`` constraints in databases which support the functionality, as
well as multi-column primary keys.


Composite fields provide a property which allows the value of the composite
field directly on the model, and a point can be provided to the model's
``__init__`` method.

Calling the init method with both a value for the composite field _and_
a value for the subfield will raise a ``ValueError``

.. code:: python
    >>> m = MyModel(x=4, point=(5,6))

    ValueError: Multiple values for field 'x' (via keyword arguments 'x'
                and 'point')

Queries
-------

The values of a composite field must be queryable via the ``Model.objects`` API.

:`in`: Query for whether the value of the composite field is present in the
        provided list of values
:`exact`: Query for whether the value of the composite field equals the provided
          value
:`isnull`: Query for whether the value for the composite field is `None`. It is
           assumed

In addition, for each of the subfields of the composite field, a transform will
be provided which allows the user to perform a query on the subfield via the
composite field.

.. code:: python

    MyModel.objects.filter(point__x__lt=4)

would be transformed into a lookup of all point values which have an x value
less than 4.


Interactions with ``Model._meta``
--------------------------------

Since all subfields of a model are also local concrete fields of a model, they
are available via ``Model._meta.fields`` with the appropriate subfield name.

Since the composite field is virtual, it is not included in ``Model._meta.fields``,
but can be accessed via ``Model._meta.virtual_fields``. It is also possible to
retrieve a ``CompositeField`` instance via the method ``Model._meta.get_field``.

To access the ``Subfield`` instance associated with the field (rather than the
wrapped field itself), the composite field exposes a ``get_subfield`` method.

For example, given the following model:

..code:: python

  >>> class MyModel(models.Model):
  ...    x = models.IntegerField()
  ...    y = models.IntegerField()
  ...
  ...    point = models.constrain(x, y, unique=True)
  ...
  >>> MyModel.get_field('x')
  <IntegerField instance at 0x????????>
  >>> MyModel.get_field('point')
  <CompositeField instance at 0x????????>
  >>> _.get_subfield('x')
  <Subfield instance at 0x????????>

An additional argument ``include_subfields`` which defaults to ``False`` will
be added to the ``Options.get_fields`` method, which will include all subfield
instances of the model.


..code:: python

  >>> for f in MyModel._meta.get_fields():
  ...     print(f)
  <IntegerField MyModel.x>
  <IntegerField MyModel.y>
  <CompositeField MyModel.point>
  >>> for f in MyModel._meta.get_fields(include_subfields=True):
  ...     print(f)
  <IntegerField MyModel.x>
  <IntegerField MyModel.y>
  <Subfield MyModel.point.x>
  <Subfield MyModel.point.y>
  <CompositeField MyModel.point>



Motivation
==========

Django's model API provides a relatively coarse level of data abstraction,
relying upon assumption that a single userland object will map to a single
table in the database.

In addition, this API provides the groundwork for adding data abstraction over
column subsets (DEP 192) and the future implementation of multi-column primary
keys.


Backwards Incompatability
=========================

Deprecation of Model.Meta.index_together and Model.Meta.unique_together?

Reference Implementation
========================

TBA

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).

(All DEPs must include this exact copyright statement.)
