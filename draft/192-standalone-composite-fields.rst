====================================
DEP 192: Standalone Composite Fields
====================================

:DEP: 192
:Author: Thomas Stephenson
:Implementation Team: Thomas Stephenson
:Shepherd: __
:Status: Draft
:Type: Feature
:Created: 2015-03-18
:Last-Modified: 2015-03-18

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

* ``null=True`` is an acceptable argument for a standalone composite field
* ``is_tuple=True``, from composite field is an invalid argument. A standalone
  field should define the value transformation functions ``value_to_dict`` and
  ``value_from_dict``, rather than auto-coercing the value into a tuple

In addition, a standalone field constructor can accept keyword arguments which
are used to pass arguments to subfields. It is the user's responsibility to
provide an appropriate ``deconstruct`` implementation for the values of these
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

Unlike the subfields declared in DEP 191, which are proxies for other fields
declared on a model, a `managed subfield` is added to the model by the
composite field which defines it and is responsible for storing it's own value
on the model instance.

The value of a managed subfield is stored on the model with the attribute name
``composite_attname + '__' + subfield_name``, where:

* ``composite_attname`` is the attribute name of the composite field which
  manages the subfield on the model; and
* ``subfield_name`` is the name of the subfield as declared in the composite
  field declaration.

By defining the attribute name in this way, it is guaranteed to be unique
amongst all fields on the model (since ``'__'`` is an illegal substring of a
field name). It also mirrors the syntax for querying the value of a subfield,
which aids querying for instances based on the value of a subfield.


Value transformation functions
------------------------------

Composite fields declare two transformation functions, ``value_from_dict`` and
``value_to_dict``. These functions are intended to be overidden by subclasses
of CompositeField to marshal the value of the field to and from python objects.
These methods are named differently to the value transformation functions on
`Field`, due to the mismatch of parameter types and returned values.

The implementations of these functions are subject to the following
restrictions:

* ``value_to_dict`` will always be passed as argument a python `dict`, which
  maps subfield names (as defined on the composite field) to their values. It
  should return either a python object or `None`.

  The default implementation of this function is to return the value of the
  argument unchanged.
* ``value_from_dict`` can receive as argument any python object, including
  ``None``. It must return a python ``dict`` instance, with *all* subfields
  mapped to a python value appropriate for that subfield type.

  The default implementation of this function is to return the value of the
  argument unchanged, unless the argument is ``None``, in which case a
  ``ValueError`` is raised.

Restrictions on sublcassing of composite fields
-----------------------------------------------

Subclassing of ``CompositeField`` is allowed provided that only one superclass
in the mro of a class defines a concrete subfield. On one hand, the semantics of
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

Null Handling
-------------

A previous version of this proposal included a requirement that python ``None``
values on composite fields be implicitly handled by the framework. The reasoning
was that this would place less requirements on the ``value_to/from_dict``, and
simplify the implementation of ``isnull`` queries.

The first proposed solution was to include an ``isnull`` column in all composite
fields which were instantiated with ``null=True``. This was argued to result in
bad table design.

The next solution called for forcing all managed subfields to ``null=True``
when constructing a composite field with ``null=True``, however the failure to
make the change explicit could lead to unintentional dropping of constraints on
the table, an undesirable behaviour.

The current appropach is to disallow ``value_to_dict`` from returning ``None``
and to use the returned value to construct the ``isnull`` query.


Reference Implementation
========================

TBA.

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).

(All DEPs must include this exact copyright statement.)
