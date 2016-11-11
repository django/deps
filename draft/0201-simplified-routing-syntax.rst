===================================
DEP 0201: Simplified routing syntax
===================================

:DEP: 0201
:Author: Tom Christie
:Implementation Team: Tom Christie, Sjoerd Job Postmus
:Shepherd: Tim Graham
:Status: Draft
:Type: Feature
:Created: 2016-10-19
:Last-Modified: 2016-10-20

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

This DEP aims to introduce a simpler and more readable routing syntax to
Django. Additionally the new syntax would support type coercion of URL
parameters.

We would plan for this to become the new convention by default, but would do so
in a backwards compatible manner, leaving the existing regex based syntax as an
option.

Motivation
==========

Here's a section directly taken from Django's documentation on URL
configuration...

.. code-block:: python

    urlpatterns = [     
        url(r'^articles/2003/$', views.special_case_2003),
        url(r'^articles/(?P<year>[0-9]{4})/$', views.year_archive),
        url(r'^articles/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/$', views.month_archive),
        url(r'^articles/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/$', views.article_detail),
    ]

There are two aspects to this that we'd like to improve on:

* The Regex based URL syntax is unnecessarily verbose and complex for the vast
  majority of use-cases.
* The existing URL resolver system does not handle typecasting, meaning that
  all URL parameters are treated as string literals.

In order to do so we propose to implement a new URL routing option, based on
the Flask URL syntax. This is a simpler and more readable format. Unlike the
regex approach, this syntax also includes type information, allowing us to
provide for typecasting of the URL parameters that are passed to views.

The existing syntax would remain available, and there would be no plans to
place it on a deprecation path. Indeed, the underlying implementation for the
typed URL syntax would actually be to use expand the typed URLs out into the
existing Regex style, although this would largely remain an implementation
detail, rather than an exposed bit of API.

The end result is that we would like to be able to present the following
interface to our developers...

.. code-block:: python

    urlpatterns = [     
        path('articles/2003/', views.special_case_2003),
        path('articles/<int:year>/', views.year_archive),
        path('articles/<int:year>/<int:month>/', views.month_archive),
        path('articles/<int:year>/<int:month>/<int:day>/', views.article_detail),
    ]

The ``path()`` argument would also accept arguments without a converter prefix,
in which case the converter would default to "string", accepting any text
except a ``'/'``.

For example:

.. code-block:: python

    urlpatterns = [
        path('users/', views.user_list),
        path('users/<id>/', views.user_detail),
    ]

For further background, please see the `"Challenge teaching Django to beginners: urls.py" <https://groups.google.com/forum/#!topic/django-developers/u6sQax3sjO4>`_ discussion group thread.

Core vs Third-Party
===================

In our consideration this feature should be included in core Django rather than
as a third-party app, because it adds significant value and readability.

It is far more valuable when presented to the community as *the new standard*,
rather than as an alternative style that can be bolted on. If presented as a
third-party add-on then the expense of a codebase going against the standard
URL convention will likely always prevent widespread uptake.

Specification
=============

Imports
-------

The naming for the import needs to be decided on. The existing URL configuration
uses:

.. code-block:: python

    from django.conf.urls import url

The naming question would be:

* What should the new style be called? Would we keep ``url``, or would we need
to introduce a different name to avoid confusion?
* Where should the new style be imported from?

Our constraints here are that the existing naming makes sense, but we also need
to ensure that we don't break backwards compatiblility.

Our proposal is that we should use a diffrent name and that the new style should
be imported as...

.. code-block:: python

    from django.urls import path

A consistently named regex specific import would also be introduced...

.. code-block:: python

    from django.urls import path_regex

The name ``path`` makes semantic sense here, because it actually does represent
a URL component, rather than a complete URL.

The existing import of ``from django.conf.urls import url`` would become a shim
for the more explicit ``from django.urls import path_regex``.

Given that it is currently used in 100% of Django projects, the smooth path for
users would be to not deprecate its usage immediately, but to consider placing
it on the deprecation path at a later date.

Converters
----------

Flask supports the `following converters <http://flask.pocoo.org/docs/0.11/quickstart/#variable-rules>`_.

``string``
    Accepts any text without a slash (the default)
``int``
    Accepts integers
``float``
    Like ``int`` but for floating point values
``path``
    Like the default but also accepts slashes
``any``
    Matches one of the items provided
``uuid``
    Accepts UUID strings

We might also consider including `a regex converter <http://stackoverflow.com/questions/5870188/does-flask-support-regular-expressions-in-its-url-routing>`_.

Furthermore, an interface for implementing custom converters should exist. We
could use the same API as Flask's ``BaseConverter`` for this purpose. The
registration of custom converters could be handled as a Django setting,
``CUSTOM_URL_CONVERTERS``. The default set of converters should probably 
*always* be included.

Failure to perform a type conversion against a captured string should result in
an ``Http404`` exception being raised.

Adding type conversion to the existing system
---------------------------------------------

Adding a new URL syntax is easy enough, as they can be mapped onto the existing
Regex syntax. The more involved piece of work would be providing for type
conversion with the existing regex system. The type conversion functionality
would need to support both named and unnamed capture groups.

One option could be:

* Add a new ``converters`` argument to the ``url`` argument.
* The value can either be a list/tuple, in which case its elements are mapped
  onto the capture groups by position, or a dict, in which case its elements
  are mapped onto the capture groups by name. (The former case is more general
  as it supports using the positional style to correspond with either named or
  unamed groups)
* The items in the ``converters`` argument would each be instances of
  ``BaseConverter``

(An alternative might be to add separate ``converter_args`` and
``converter_kwargs`` arguments.)

We would also need to support the reverse side of type conversion. Ensure that
reverse can be called with typed arguments as well as string literals.

Preventing unintended errors
----------------------------

*The following behaviour is not necessary, and we might not choose to add
this. However, it is worth considering a way to guard against user error...*

Even with differently named functions there remains some potential for user
error. For example:

* A developer using Django's new URL system accidentally uses
  ``from django.conf.urls import url``, and fails to notice the error. They are
  unaware that they are using regex URLs, not typed URLs, and cannot determine
  why the project is not working as expected.
* A developer who is continuing to use regex URLs incorrectly uses the
  ``fram django.urls import path`` and fails to notice the error. They are
  unaware that they are using typed URLs, not regex URLs, and cannot determine
  why the project is not working as expected.

One way to guard against this would be to:

* Enforce that new style ``path()`` arguments must not start with a leading
  ``'^'``.
* Enforce that old style ``url()`` arguments must start with a leading ``'^'``.

This behaviour would ensure that the two different cases could not be used
incorrectly.

There is a decidedly edge-case deprecation that this would introduce in that
existing projects that happen to *intentionally* include an unachored URL regex
would raise a ``ConfigurationError`` when upgraded. However this is a loud and
documentable error, with a simple resolution. (Change the import to
``from django.urls import path_regex``.)

Internal ``RegexURLPattern`` API
================================

New style URLs should make the original string available to introspection using
a ``.path`` attribute on the path instance.

They should be implemented as a ``TypedURLPattern`` that subclasses
``RegexURLPattern``.

These are aspects of the internal API, and would not be documented behaviour.

Documentation
=============

The new style syntax would present a cleaner interface to developers. It would
be beneficial for us to introduce the newer syntax as the primary style, with
the existing regex style as a secondary option.

It is suggested that we should update all URL examples accross the
documentation to use the new style.

Implementation tasks
====================

The following independent tasks can be identified:

* Implement the ``converters`` argument. This adds the low-level API support
  for type coercion. Ensure that lookups perform type coercion, and
  correspondingly, that calls to ``reverse`` work correctly with typed
  arguments.
* Add support for the new style ``path`` function, with an underlying
  implementation based on the regex urls.
* Add ``path_regex``, with ``from django.conf.urls import url`` becoming a shim
  for it.
* Add support for registering custom converters, as defined in the Django
  settings.
* Document the new style URL configuration.
* Update existing URL cases in the documentation throughout.
* Update the tests throughout, updating to the new style wherever possible.

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).
