======================
DEP XXXX: Rejuvenate form media
======================

:DEP: XXXX
:Author: Thibaud Colas
:Implementation Team: You? People in the `forum thread: Rejuvenating vs deprecating Form.Media <https://forum.djangoproject.com/t/rejuvenating-vs-deprecating-form-media/21285>`_
:Shepherd: You?
:Status: Draft
:Type: Feature
:Created: 2023-12-12
:Last-Modified: 2023-12-19

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

See `forum thread: Rejuvenating vs deprecating Form.Media <https://forum.djangoproject.com/t/rejuvenating-vs-deprecating-form-media/21285>`_.
We want `form.Media <https://docs.djangoproject.com/en/5.0/topics/forms/media/>`_ to catch up with modern web standards, so Django projects can more easily leverage those standards.

Specification
=============

See the `MDN script element documentation <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/script>`_ and `link element documentation <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/link>`_.

Here are requirements which Django could/should better support:

- ES modules
- Import maps
- Dynamic module imports
- async, defer scripts
- CSPs via nonce attributes
- integrity attribute
- fetchpriority attribute
- nomodule attribute
- Arbitrary script attributes
- Preloading / speculative loading
- Resource ordering (see `capo.js <https://rviscomi.github.io/capo.js/>`_)
- Web Components


Motivation
==========

`form.Media <https://docs.djangoproject.com/en/5.0/topics/forms/media/>`_ is a good API to manage a form widget’s dependencies.
Though not all projects need to keep a strict record of each widget’s dependencies

Rationale
=========

This section should flesh out out the specification by describing what motivated
the specific design and why particular design decisions were made.  It
should describe alternate designs that were considered and related work.

The rationale should provide evidence of consensus within the community and
discuss important objections or concerns raised during discussion.

Backwards Compatibility
=======================

At this stage I wouldn’t expect this to introduce any backwards-incompatible changes. If we did so, it would be with a very gradual deprecation path, likely only in the interest of:

- Better performance (for example default to more modern script loading techniques)
- Better security (for example default to… more modern script loading techniques)

Reference Implementation
========================

Here are the most fully-fledged implementations so far:

- https://github.com/matthiask/django-js-asset/
- https://github.com/rails/importmap-rails

Other references:

- https://github.com/dropseed/django-importmap
- https://github.com/tonysm/importmap-laravel

TODOs
=====

- Add more possible requirements
- Review https://github.com/wsvincent/awesome-django for packages with form media-related functionality.
- Review https://djangopackages.org/ for packages with form media-related functionality.
- Update https://github.com/st3v3nmw/awesome-django-performance with existing performance-related Django packages relating to form assets.
- Also update https://github.com/wsvincent/awesome-django with good packages in this category

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).
