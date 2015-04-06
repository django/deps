=========================
DEP 191: Composite Fields
=========================

:DEP: 191
:Author: Thomas Stephenson
:Implementation Team: Thomas Stephenson
:Shepherd: Anssi Kääriäinen
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

The value of a ``CompositeField`` on a model instance is an unordered  python
``dict``, mapping subfield names to their respective values on the model. This
may seem restrictive, but an API which provides the ability to store the values
of composite fields as aribitrary python objects is proposed as part of DEP 192.


Subfield
--------

A *subfield* of a composite field is a field which exists on the model and which
stores the value of at most one of the composite field's database columns on
the model.


Data Binding
------------

When the value of a composite field is accessed on a model, a new object is
created which reflects the current value of the field. Over the lifetime of
the object, it is possible for the value of the composite field and the
subfields to become unsynced, causing potential bugs and data corruption.

The proposed solution to this problem is to implement data binding between
the items of the value of a composite field and it's subfields.


** TODO: Discuss **
The data binding is strictly one way, so if a value of the attribute/item
on the composite field's value is updated, the subfield's value will also be
updated accordingly, but the composite field will be insensitive to any updates
to the subfield's value.

Two way data binding is possible, but would require more extensive (possibly
breaking?) changes to the field API and make it more difficult to debug
dataflow problems.

Observer
~~~~~~~~

An observer is an informal python interface which specifies a type as able to
respond to a change in a bound property of an observable it is watching. Any
class which implements the following methods will be considered a conforming
observer.

.. code:: Python

    class Observer(object):
        def watch(self, observable, bound=None):
            """
            Add `self` to the list of observers of `observable`.

            If `observable` is a `dict`, `bound` is a set of items to watch.
            If `observable` is a `tuple`, `bound` is a set of indicies to watch.
            Otherwise, `bound` is a set of attribute names.

            If `attrs` is `None`, the observer is notified for every change of
            an attribute or item of the observable.
            """
            return NotImplemented

        def notify_change(self, observable, bound_name, old, new):
            """
            Called whenever bound value on the watched observable `observable`
            changes.
            """
            return NotImplemented


Changes to fields
~~~~~~~~~~~~~~~~~

All django fields (except relations) will be updated to implement the observer
interface. ``notify_change`` will be implemented so that when the ``bound_name``
matches the name of the field, the field's value will be updated on the model.

Assigning an observable object to a foreign model will immediately sync the
values of all subfields on the foreign model and add the subfields on the
foreign model as observers.


ObservableDict
~~~~~~~~~~~~~~

The value of a composite field will be returned as a subclass of ``dict``, with
the item ``subfield_name`` bound to the corresponding subfield. Copying the
object (by eg. calling `dict` on the result) will detach it from any observers.



Providing a constraint that spans multiple columns
--------------------------------------------------

A new top-level function will be added to the models API with the following
signature

.. code:: Python

    def constrain(*fields, unique=False, index=True)

The ``constrain`` function will create a `CompositeField` in the model and add
subfields to the composite field in the order in which they appear in the
argument list.

.. code:: python

    class MyModel(models.Model):
        x = models.IntegerField()
        y = models.IntegerField()

        point = models.constrain(x, y, unique=True)

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
