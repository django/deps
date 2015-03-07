=========================
DEP 191: Composite Fields
=========================

:DEP: 191
:Author: Thomas Stephenson
:Implementation Team: Thomas Stephenson
:Shepherd: __
:Status: Draft
:Type: Feature
:Created: 2015-03-06
:Last-Modified: 2015-03-06

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

Define a new type of virtual field which maps onto one or more concrete
database fields in the model's table. These fields can be used to define
table constraints which span multiple columns with greater locality than if the
same constraints were created using the current `index_togther` or
`unique_together` APIs.

Specification
=============

CompositeField
--------------

A `CompositeField` is a new virtual field type which combines multiple columns
on a model's table into a single object, which is accessible from model
instances.

The value of a `CompositeField` on a model instance is either, depending on

* A dict, mapping subfield values to their values on the model
* A tuple of the field's subfield values

depending on the value of `field.is_tuple_value`.

Subfield
--------

A subfield is a proxy for another field. Subfields are ordered by the time
they were added to the composite field.

The value for a subfield on a model instance is the same as the value
for the proxied field.



Providing a constraint that spans multiple columns
--------------------------------------------------

*FIXME*:
    Does it make sense to create table indexes using `constrain`? Can we
    support `CHECK` constraints too?

A new top-level function will be added to the models API with the following
signature

.. code:: Python

    def constrain(*fields, unique=False, index=True, is_tuple=False)

The `constrain` function will create a `CompositeField` in the model and add
subfields to the composite field in the order in which they appear in the
argument list.

eg.

.. code:: python

    class MyModel(models.Model):
        x = models.IntegerField()
        y = models.IntegerField()

        point = models.constrain(x, y, unique=True, is_tuple=True)

This code inserts a composite field, with the name `point` to the model. A
constraint which ensures the uniqueness of the point will be added to the table
and an index will be added to the

.. note::

    Composite fields provide a property which allows the value of the composite
    field directly on the model, and a point can be provided to the model's
    `__init__` method.

    Calling the init method with both a value for the composite field _and_
    a value for the subfield will raise a `ValueError`

    e.g.

    .. code:: python

        >>> m = MyModel(x=4, point=(5,6))

        ValueError: Multiple values for field 'x' (via keyword arguments 'x'
                    and 'point')

Queries
-------

The values of a composite field must be queryable via the `Model.objects` API.

:`in`: Query for whether the value of the composite field is present in the
        provided list of values
:`EXACT`: Query for whether the value of the composite field equals the provided
          value

In addition, for each of the subfields of the composite field, a transform will
be provided which allows the user to perform a query on the subfield via the
composite field.

e.g.

..code:: python

    MyModel.objects.filter(point__x__lt=4)

would be transformed into a lookup of all point values which have an x value
less than 4.


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
