===================================
DEP 0201: Simplified routing syntax
===================================

:DEP: 0201
:Author: Tom Christie, Sjoerd Job Postmus, Aymeric Augustin
:Implementation Team: Sjoerd Job Postmus
:Shepherd: Aymeric Augustin
:Status: Final
:Type: Feature
:Created: 2016-10-19
:Last-Modified: 2017-09-30

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

This DEP aims to introduce a simpler and more readable routing syntax to
Django. Additionally the new syntax supports type coercion of URL parameters.

We plan for this to become the new convention by default, but in a backwards
compatible manner, leaving the existing regex based syntax as an option.

Motivation
==========

Here's a section directly taken from Django's documentation on URL
configuration:

.. code-block:: python

    urlpatterns = [
        url(r'^articles/2003/$', views.special_case_2003),
        url(r'^articles/(?P<year>[0-9]{4})/$', views.year_archive),
        url(r'^articles/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/$', views.month_archive),
        url(r'^articles/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/$', views.article_detail),
    ]

There are two aspects to this that we'd like to improve on:

* The regex-based URL syntax is unnecessarily verbose and complex for the vast
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
existing regex style, although this would largely remain an implementation
detail, rather than an exposed bit of API.

The end result is that we would like to be able to present the following
interface to our developers:

.. code-block:: python

    urlpatterns = [
        path('articles/2003/', views.special_case_2003),
        path('articles/<int:year>/', views.year_archive),
        path('articles/<int:year>/<int:month>/', views.month_archive),
        path('articles/<int:year>/<int:month>/<int:day>/', views.article_detail),
    ]

The ``path()`` argument would also accept arguments without a converter
prefix, in which case the converter would default to ``string``, accepting any
text except a ``'/'``.

For example:

.. code-block:: python

    urlpatterns = [
        path('users/', views.user_list),
        path('users/<name>/', views.user_detail),
    ]

For further background, please see the
`Challenge teaching Django to beginners: urls.py
<https://groups.google.com/forum/#!topic/django-developers/u6sQax3sjO4>`_
discussion group thread.

Specification
=============

Imports
-------

The existing URL configuration uses:

.. code-block:: python

    from django.conf.urls import url

The naming questions are:

* What should the new style be called? Would we keep ``url``, or would we
  introduce a different name to avoid confusion?
* Where should the new style be imported from?

Our constraints here are that the existing naming makes sense, but we also
need to minimize confusion, especially during the transition period, and to
ensure that we don't break backwards compatibility.

We propose to use a different name and to take this opportunity to simplify
the import path:

.. code-block:: python

    from django.urls import path

The regex version would be renamed consistently and made available as:

.. code-block:: python

    from django.urls import re_path

The name ``path`` makes semantic sense here, because it actually does represent
a URL component, rather than a complete URL.

The existing import of ``from django.conf.urls import url`` would become a
shim for the more explicit ``from django.urls import re_path``.

Given that it is currently used in 100% of Django projects, the smooth path
for users would be to not deprecate ``django.conf.urls.url`` immediately, but
to mark it as deprecated in version 3.0 (after 2.2 LTS) and remove it in 4.0
(after 3.2 LTS). Hopefully many projects will migrate to ``django.urls.path``
(the carrot) before being forced to migrate to ``django.urls.re_path`` (the
stick).

Converters
----------

Django will support the following converters out of the box:

``string``
    Accepts any text without a slash (this is the default converter)
``int``
    Accepts non-negative integers
``path``
    Accepts any text
``slug``
    Accepts ASCII-only slugs, based on the same definition as ``SlugField``
``uuid``
    Accepts UUIDs

Failure to perform a type conversion against a captured string is interpreted
as if the given path does not match the URL.

Furthermore, an interface for registering custom converters will be provided:

.. code-block:: python

    from django.urls import register_converter

    register_converter(Converter, 'conv')

Users are expected to call ``register_converter`` in their URLconf module, to
make sure converters are registered before the URLconf is loaded.

Since the set of converters a project may need seems relatively narrow, there
are no provisions for avoiding name clashes at this point. Namespacing would
make converter names in URL patterns long, at the expense of readability.

If name conflicts turned out to be a problem for pluggable apps, then a
``converters`` keyword argument could be added to the ``path()`` function. It
would allow specifying converters for each pattern, overriding any globally
declared converters with conflicting names.

Providing a ``register_converter`` function rather than a global setting keeps
the global state within the ``django.urls`` module and minimizes the distance
between where converters are declared and where they're used.

No ``unregister_converter`` function will be implemented because there's no
clear use case at this point. It could be added if the need arises.

Defining type conversions
-------------------------

A converter is a class with one attribute and two methods.

``regex``
    The pattern to use in place of the type specifier.
``to_python``
    How to convert the string from the URL to a Python object.
``to_url``
    How to convert the Python object back to something suitable in a URL.

For instance, a converter for handling with the ``int`` parameter can be
defined as follows.

.. code-block:: python

    class IntConverter(object):
        regex = '-?[0-9]+'

        def to_python(self, value):
            return int(value)

        def to_url(self, value):
            return str(value)

Here, ``to_python`` is going to be called as part of ``resolve`` while
``to_url`` will be called during ``reverse``.

If ``to_python`` raises a ``ValueError``, it will be interpreted as if the
given path does not match the URL, and resolving will continue. This gives the
ability to deal with cases where the validity of the content can not easily or
fully be described using a regular expression alone. No other exceptions are
caught.

The method ``to_url`` will always be called, no matter the type of ``value``.
In particular, it will be called even when ``value`` is a string. This allows
one to implement—for instance—a ``base64`` converter or a converter that works
with signed values as handled by ``django.core.signing.TimestampSigner``. The
return value of ``to_url`` must not be URL-encoded.

Adding type conversion to the existing system
---------------------------------------------

Adding the new URL syntax is easy enough, as it can be mapped onto the
existing regex syntax. The more involved piece of work is providing for type
conversion with the existing regex system.

We propose that the type conversion (at first) only works for named capture
groups. This because the ``path`` function only builds named capture groups.

In practice, this means:

* Adding a new ``converters`` argument to the ``url`` function. This argument
  is intended to be a private-but-stable API, rather than documented.
* The value of the ``converters`` argument is a dictionary, with keys
  corresponding to capture group names and the corresponding values being
  instances of ``BaseConverter`` (or something that duck-types the same way).
* The type specifiers as supplied in the arguments to ``path`` will be used to
  build the ``converters`` argument for ``re_path``.

Type conversions and ``reverse``
--------------------------------

To support the ``reverse`` method on ``path``-based routes, the type converters
will have to supply a ``to_url`` method which does the reversing. There will be
no support for passing ``converter.to_url(value)`` to ``reverse``, because some
``to_url`` functions might actually have text as input.

As an implementation detail, the plan is to call ``converter.to_url`` instead
of ``force_text`` in ``_reverse_with_prefix``. The downside is that the
conversion now has to happen inside a loop, instead of only once, which might
have performance drawbacks.

Implementation
==============

Documentation
-------------

The new style syntax presents a cleaner interface to developers. It will be
beneficial for us to introduce the newer syntax as the primary style, with the
existing regex style as a secondary option.

All URL examples across the documentation will be updated to the new style.

Tasks
-----

The following independent tasks can be identified:

* Implement several ``Converters``, and document the API.
* Add support for the new style ``path`` function, with an underlying
  implementation based on the regex URLs.
* Add ``re_path``, with ``from django.conf.urls import url`` becoming a shim
  for it.
* Implement the ``converters`` argument. This adds the low-level API support
  for type coercion. Ensure that lookups perform type coercion, and
  correspondingly, that calls to ``reverse`` work correctly with typed
  arguments.
* Add support for registering custom converters.
* Add dedicated tests for both the old and new style, so there's adequate
  coverage. Currently only URL reversing is tested. URL resolution is only
  exercised as a side effect of unrelated tests.
* Ensure the 404 debug page shows URLs in a style that matches the URLconf.
* Document the new style URL configuration.
* Update existing URL cases in the documentation throughout.
* Update the tests throughout, updating to the new style wherever possible.

Internal ``RegexURLPattern`` API
--------------------------------

New style URLs should make the original string available to introspection using
a ``.path`` attribute on the path instance.

They should be implemented as a ``TypedURLPattern`` that subclasses
``RegexURLPattern``.

These are aspects of the internal API, and would not be documented behaviour.

Rationale
=========

Core vs Third-Party
-------------------

This feature should be included in core Django rather than as a third-party
app because it adds significant value and readability.

It is far more valuable when presented to the community as *the new standard*,
rather than as an alternative style that can be bolted on. If presented as a
third-party add-on then the expense of a codebase going against the standard
URL convention will likely always prevent widespread uptake.

Some contributors would prefer a more generic, pluggable URL routing system.
The authors of this DEP believe implementing this feature directly in Django
is a better trade-off. A longer argumentation is available in `this message
<https://groups.google.com/d/msg/django-developers/D44LSp0bPg8/hKybIqNiBAAJ>`_
to the discussion group.

Related projects
----------------

Marten Kenbeek has been working on `refactoring the dispatcher API
<https://github.com/knbk/django/tree/dispatcher_api>`_. That effort is
currently stalled and there is no schedule for completing it.

It tackles the problem at a different level. It aims to make it possible to
replace the whole URL resolver. As a consequence, it's fairly independent
from this DEP, which proposes much more limited and pragmatic changes.

Routing on different aspects
----------------------------

`Django Hosts <http://django-hosts.readthedocs.io/en/latest/>`_ allows for
routing based on the host aspect of a request. Django Channels has a message
routing layer, which can inspect different aspects of the messages.

While it would be a good idea to see if the routing layer can be augmented to
remove the need for ``django-hosts`` and be useful for Channels, it is our
opinion that these are orthogonal concerns. Due to the expected implementation
burden to also support these concerns, it is our preference that this is to be
reconsidered at a later point in time, as to not delay the progress on the
simplified routing syntax.

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).
