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

Uses the `CompositeField` field type defined in `DEP 191` to add the capability
of providing data abstractions over a subset of concrete fields of a model.
This provides the capability of sharing groups of fields which commonly appear
together on a model, as well as an opportunity to hide implementation details
associated with the fieldset.

Specification
=============

This specification liberally uses the terminology defined in `DEP 191` to refer
to aspects of the composite fields API.

Syntax
------

Providing a Standalone composite field declaration is very similar to defining
a django model, except that instead of subclassing `django.db.models.Model`,
the class extends `django.db.models.CompositeField`.

eg.

.. code:: python

    from django.db.models import CompositeField
    from my_money import Money

    class MoneyField(models.CompositeField):
       currency_code = models.CharField(max_length=3)
       amount = models.DecimalField()

    class RetailItem(models.Model):
        price = MoneyField()


The `currency_code` and `amount` fields in the example above are _managed_
subfields, and are contributed to the `RetailItem` model by the `MoneyField`
class.

Migrations of managed subfields are handled and deconstructed by the composite
field, rather than during model deconstruction.


Field parameters
----------------

All of the parameters defined by `Field` and `CompositeField` are accepted
by a standalone composite field with the following provisos:

* `null` is an acceptable argument for a standalone composite field
  (see :Handling python None:)
* `is_tuple`, from composite field is an invalid argument. A standalone
  field should define the value transformation functions `value_to_dict` and
  `value_from_dict`, rather than auto-coercing the value into a tuple

In addition, a standalone field constructor can accept keyword arguments which
are used to pass arguments to subfields. It is the user's responsibility to
provide an appropriate `deconstruct` implementation for the values of these
extra arguments.

eg.

.. code:: python

   class MoneyField(models.CompositeField):
        ...

        def __init__(self, amount_max_digits=None, amount_decimal_places=None, **kwargs):
            amount = self.get_subfield('amount')
            amount.max_digits = amount_max_digits
            amount.decimal_places = amount_decimal_places

        def deconstruct(self):
            name, path, args, kwargs = super(MoneyField, self).deconstruct()
            kwargs['amount_max_digits'] = self.amount.max_digits
            kwargs['amount_decimal_places'] = self.amount.decimal_places


Managed Subfields
~~~~~~~~~~~~~~~~~

*TODO:*
Some information about managed subfields



Value transformation functions
------------------------------

Composite fields declare two transformation functions, `value_from_dict` and
`value_to_dict`. These functions are intended to be overidden by subclasses
of CompositeField to marshal the value of the field to and from python objects.
These methods are named differently to the value transformation functions on
`Field`, due to the mismatch of parameter types and returned values.

These methods are expected to handle python `None` correctly if `None` is
allowed as a value for the `CompositeField` (see :Null handling:).

The default implementation of both these functions is to return the argument
unchanged.


Restrictions on sublcassing of composite fields
-----------------------------------------------

Subclassing of `CompositeField` is allowed provided that only one superclass in
the mro of a class defines a concrete subfield. On one hand, the semantics of
inheritance of django models is complex enough without complicating it further
by allowing inheritance of subfields. On the other hand, it can be desirable
to customise the python behaviour of composite fields, or to provide python
behaviour which may be shared between the implementation of different composite
fields.

.. code:: python

    >>> class A(models.CompositeField):
    ...    a_field = models.IntegerField()
    ...
    >>> class B(A):
    ...    b_field = models.IntegerField()

    TypeError: At most one class in the inheritance heirarchy of B can define a
               subfield.

Null Handling
-------------

Often, it is desirable to allow a `CompositeField` to be associated with a
python `None` value, while enforcing `NOT NULL` constraints on the columns.
If the `null` field parameter is passed to a `CompositeField` constructor, an
implicit `field__isnull` column into the model's table and this value will be
used to determine whether a null value should be returned when querying or
accessing the fields value.

Attempting to allow null values on a composite field while not providing a
`default` for any of the subfields is a field error.

e.g.

..code:: python

    >>> class Money(models.CompositeField):
    ...     currency_code = models.CharField(max_length=3, default='USD')
    ...     amount = models.DecimalField()
    ...
    >>> m = MoneyField(null=True)
    >>> m.check()

    FieldError: No `default` value provided for subfield Money.amount

Queries
-------

Standalone composite fields will support all the values


Motivation
==========

Django's models provide a relatively coarse level of abstraction. A core
assumption associated with the implementation of models is that there is a
strict one-to-one mapping of database tables to python objects in the model
domain.

However, in practice, there are often cases where one or more related field
definitions which would naturally define a python object, but for which it would
be impractical or inefficient to define as a seperate model.

This specification attempts to provide an API for defining these types of
abstractions to the django orm.

Rationale
=========

TBA.


Reference Implementation
========================

TBA.

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).

(All DEPs must include this exact copyright statement.)
