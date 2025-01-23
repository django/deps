DEP 0015: Content type aware parsing and modernization of the HttpRequest API
=============================================================================

:DEP: 0015
:Author: David Smith
:Implementation Team: TBC
:Shepherd: TBC
:Status: Draft
:Type: Feature
:Created: 2024-03-25
:Last-Modified: 2024-05-29

.. contents:: Table of Contents
   :depth: 3
   :local:


Abstract
========

Currently Django can parse requests for ``application/x-www-form-urlencoded`` and ``multipart/form-data`` types. Other types, such as JSON are currently returned as a string.

This DEP proposes to add configurable content type parsers to allow parsing of additional content types. It is proposed that Django will include a parsing of JSON, and appriate hooks to allow users to add custom parsers for other content types.

Parsed data from an ``HttpRequest`` is currently accessed via its ``POST`` attribute. It would be a breaking change if Django were to start parsing content types where currently a string is returned. To avoid introducing a breaking change it is proposed that a new ``data`` attribute is added for the new behaviour.

While introducing a new name for ``POST`` it is proposed that the names for the other attributes are modernized with an equivalent behaviour:

* ``GET`` -> ``query_params``
* ``POST`` -> ``form_data``
* ``COOKIES`` -> ``cookies``
* ``META`` -> ``meta``
* ``FILES`` -> ``files``

The existing ``GET``, ``POST``, ``COOKIES``, ``META``, and ``FILES`` attributes will be maintained for backwards compatibility, and the behaviour will remain unchanged.

Specification
=============

Django shall provide parsers for ``application/x-www-form-urlencoded``, ``multipart/form-data`` and ``application/json`` content types.

A parser should be a class which is instantiated with a request and have two methods.

- ``can_handle()`` should accept one argument being the ``media_type`` attempting to be parsed and returns a boolean to indicate if this parser can parse the given media type.
- ``parse()`` accepts one argument being the ``data`` to parse and returns the parsed data.

By default all requests shall be parsed by Django's default parsers. But to ensure backward compatability the new behaviour shall only be available when accessing the parsed response via the new ``data`` attribute.

The new ``data`` attribute should parse requests in as close a way as possible to the current ``POST`` attribute. In addition it shall:

* Parse ``application/JSON....`` types.
* For ``multipart/form-data`` types each part will be parsed with the appropriate parser, if available.
* Raise an ``UnsupportedMediaType`` (415) error if an unsupported content type is attempted to be parsed.

The new data attribute is therefore not 100% equivalent to POST since it will parse JSON (and other data types as parsers for those are configured) where POST would return a string.

Custom parsers for additional content types shall be supported. To allow this it is proposed that ``HttpRequest`` adds a new property which returns a list of parsers to be used when attempting to parse a request.
The list of parsers to be used can be set on the request, but must be done before ``data`` or ``FILES`` is accessed. This could be done in a middleware or in a view. For example::

    def index(request):
        request.parsers = [MyCustomParser(), FormParser(), ...]
        ...

To mitigate backward compatability concerns the new behaviour shall be accessed using the new ``data`` attribute.

At the same time it is proposed that the following attributes shall be added to modernise the other names:

* ``GET`` -> ``query_params``
* ``POST`` -> ``form_data``
* ``COOKIES`` -> ``cookies``
* ``META`` -> ``meta``
* ``FILES`` -> ``files``

The behaviour of renamed attributes shall be 100% compatible with the existing attributes. To ease migration to the new names django-upgrade can be used to automate refactoring code. Some work to show this is possible is available [1].

[1] https://github.com/smithdc1/django-upgrade/commit/c043761cb2fa00e97c3ea205be7e79fcec6f075d

Motivation
==========

This DEP is needed to add configurable content type parsing to Django. While this is likely to be well received the proposal also suggests adding new aliases which is more controversial.

The motivation to improve the names is that ``request.GET`` and ``request.POST`` are misleadingly named:

* ``GET`` contains the URL parameters and is therefore available whatever the request method. This often confuses beginners and "returners" alike.

* ``POST`` contains form data on ``POST`` requests, but not other kinds of data from ``POST`` requests. It can confuse users who are posting JSON or other formats.

Additionally both names can lead users to think e.g. "if request.GET:" means "if this is a GET request", which is not true.

The CAPITALIZED naming style is similar to PHP's global variables $_GET, $_POST, $_FILES etc. (https://www.php.net/manual/en/reserved.variables.get.php ). It stands out as unpythonic, since these are instance variables and not module-level constants (as per PEP8 https://www.python.org/dev/peps/pep-0008/#constants).

However, with ``HttpRequest`` being such a core part of Django renaming these will cause a large amount of churn. The change to the documentation will be significant and many existing tutorials, blog posts and books by authors in the community would require updating to reflect the new, recommended appraoch.
As such it is proposed that the new names are not immediately deprecated.

See mailing list conversation [2]

[2] https://groups.google.com/g/django-developers/c/Kx8BfU-z4_E/m/gJBuGeZTBwAJ

Rationale
=========

The main objection received by the community is the renaming of the attributes. This causes a lot of churn in documentation to rename attributes where the behaviour of these is equivielent.

Other options are:

- Leave additional content type parsing to 3rd party packages, e.g. DRF
- Introduce content type parsing and only add the new ``data`` attribute.

The new names for unchanged attributes is proposed as it's considered this a worthwhile improvement in its own right and introduces consistent naming across ``HttpRequest`` attributes. That is, without renaming the change only the new ``data`` attribute would be an outlier.

Backwards Compatibility
=======================

This DEP is designed to be backward compatible. The existing ``GET``, ``POST``, ``META``, and ``FILES`` attributes will be maintained for backwards compatibility, and (to emphasise again) the behaviour (specifically of POST) will remain unchanged.

This is similar to the way the headers property was added, whilst maintaining the older dictionary style lookup.

Reference Implementation
========================

There are currently two PRs which are work towards implementation of this DEP.

* Addition of content type parsing https://github.com/django/django/pull/17546
* Modernization of Request Object attribute names https://github.com/django/django/pull/17624

Copyright
=========

This document has been placed in the public domain per the Creative Commons CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).

