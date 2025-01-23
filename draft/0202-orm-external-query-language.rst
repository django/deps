===================================
DEP 202: DEP Purpose and Guidelines
===================================

:DEP: 202
:Author: Alexey Zankevich
:Shepherd: Anssi Kääriäinen, Josh Smeaton
:Status: Draft
:Type: Feature
:Created: 2017-03-29
:Last-Modified: 2017-03-29

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

Provide API in Django ORM to support third-party libraries for custom query
languages.

Motivation
==========

The Current Query Syntax
------------------------


The current simple query syntax based on keyword arguments looks a bit outdated
nowadays. Despite it has some pros, there are several disadvantages:

1. Long strings is hard to read, especially if we have fields with underscores.
It's really easy to make a mistake by missing one:

>>> GameSession.objects.filter(user_profile__last_login_date__gte=yesterday)

It's not easy to say whether it should be "user_profile" attribute or
user.profile foreign key.

2. Query strings can't be reused, thus the approach violates DRY principle.
For example, we need to order results by last_login_date:

>>> GameSession.objects.filter(user__profile__last_login_date__gte=yesterday) \
	.order_by('user__profile__last_login_date')

We can't keep user__profile_login_date as a variable as in the first part of the
expression we use a keyword argument, meanwhile in the second part - just a
string. And thus we just have to type query path twice.

3. Lookup names are not natural to Python language and require to be remembered
or looked up in documentation. For example, "__gte" or "__lte" lookups tend to be
confused with "ge" and "le" due to similarity to methods "__ge__" and "__le__".

4. Django ORM lookups don't have uniform approach how to pass multiple
parameters.
In this example they passed as tuple:

>>> Entry.objects.filter(pub_date__range=(start_date, end_date))

Or encoded into keyword parameter:

>>> Post.objects.filter(tags__276='javascript')

We can implement a generic API in Django ORM to support external query
languages, which will allow to write third-party libraries with own lookup
syntax.

Possible Third-Party Query Language
-----------------------------------

Below described how third-party query language can look like. Those examples
use abstract "QL" library.

Simple query

>>> Article.objects.filter(QL.pub_date == today)

Python comparison operators

>>> Article.objects.filter(QL.pub_date >= yesterday)

Lookup with mulitple arguments

>>> Article.objects.filter(QL.pub_date.range(yesterday, today))

Lookup with transforms

>>> Article.objects.filter(QL.title.lower() == 'hello')

Lookup with transforms with parameters

>>> Article.objects.filter(QL.author.firstname.substring(from=5) == 'akaariai')

Chained transforms

>>> Article.objects.filter(QL.title.collate('fi').lower() == 'hello')


Implementation
==============

API Interface
-------------

The existing .filter method will accept objects implementing a special
.build_expression method, which returns a ready to use expression.

.. code-block:: python

    class MyExpressionBuilder:
        def build_expression(self, model_helper):
            return MyExpression()

As expressions take field or other expressions as their init parameters, we need
a special model helper passed to build_expression function to resolve target
field.

>>> QL.user.name == 'alex'
<EqualExpressionBuilder>

So, comparison returned an expression builder, we don't care how, as it's a
third-party library. We only care about builder, which will be passed
to .filter method

.. code-block:: python

    from django.db.models import Value
    from django.db.models.lookups import Exact


    class EqualExpressionBuilder:
        def __init__(self, value):
            self.value = value

        def build_expression(self, model_helper):
            field = model_helper.get_field()
            return Exact(field, Value(self.value))

If we pass expression builder to filters instead of expressions instances,
it will require less job on query language side. For example, resolving field
will be done on ORM side, also it will allow the ORM to perform joins that will
be used by query language. Thus the third-party library
will just define query syntax and pass responsibility for all complicated and
fragile code to Django ORM.

Implementation In Django
------------------------

Currently keyword arguments are translated into a set of expressions in Query
class. There is a fat "build_filter" method which do all the magic by parsing
keyword key and trying to guess which part is lookup/transform or nested field.
Also there are some functionality related to keyword keys normalization, for
example, .filter(user_profile__create_date=None) will be internally translated
into .filter(user_profile__create_date__isnull=True).
The part of that functionality will not make sense for already prepared
expressions, however it will be necessary to resolve the joins. For that
purposes ModelHelper (the class providing .get_field method) can register
all the mentioned fields.

To be discussed which option is the best:

1. To register all the ModelHelper.get_field calls implicitly for further joins.
2. Or we just need to make two methods .get_field and .register_field?
   The first one will just return field, the second - register field for joins.
   Expression builder will be responsible to correctly register all the used
   fields.

So, summing up the process, query will be performed in next steps:

1. External language will return expression builder instance.
2. ORM will evaluate .build_expression method and register used fields for
   joins.
3. The generated expression instance will update WHERE clause and joins, which
   will be used later by SQL compiler.


Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (https://creativecommons.org/publicdomain/zero/1.0/deed).
