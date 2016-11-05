========================
DEP 7: Dependency Policy
========================

:DEP: 7
:Author: Jacob Kaplan-Moss
:Implementation Team: Jacob Kaplan-Moss
:Shepherd: Jacob Kaplan-Moss
:Status: Draft
:Type: Process
:Created: 2016-06-06
:Last-Modified: 2016-09-29

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

This DEP outlines Django's policy on external dependencies (e.g. other Python
packages required to run Django). It supersedes Django's previous, unwritten
policy of "no external dependencies allowed."

In a nutshell, the policy is that adding a new external dependency should be
treated similarly to adding a major new feature to Django: it requires a
demonstration that the dependency is needed, and rough consensus among the
community and core team that the chosen dependency is the correct one. If the
dependency is controversial, it may require a DEP and a decision by the
Technical Board.

The rest of this document explains some background and motivation to this
policy, and outlines in more details the guidelines on determining if a new
dependency is acceptable.

Background and Motivation
=========================

.. FIXME: this is too much throat-clearing. It should be pared down into just a
.. short "motiviation" section and the longer background moved to a "background"
.. section below.

When Django was first being developed, Python packaging was in its infancy.  By
the time of Django's first release (July 2005), the shape of Python's modern
packaging infrastructure was starting to emerge [1]_: PyPI had been around for a
couple of years (since 2003), and in 2005 Setuptools added the ``easy_install``
command, allowing users to automatically download and install packages from
PyPI, including dependencies.

.. [1] For more information on the early history of Python packaging, see
       `this wonderful timeline <http://blog.startifact.com/posts/older/a-history-of-python-packaging.html>`_ that Martijn Faassen wrote up.

However, Python packaging circa 2005 was just as rough around the edges as
Django was at that time. ``virtualenv`` didn't exist yet, and system-wide
installs were the norm (and just as problematic then as now). PyPI had
occasional downtime, leading to frustration when trying to deploy to production.
``easy_install`` failed in many corner cases. One of Django's early releases
(0.91) required installation via ``easy_install`` and ``setuptools``, and it
didn't go well. Many users struggled even to get the package installed.

That experience led to a deep suspicion of Python packaging tools among the
Django core team, and a de-facto policy emerged of only requiring the lowest
common denominator: installation via direct download and ``python setup.py
install``. This meant not using any of Python's packaging features developed
since about 2002, including most notably dependencies. In 2016, Django's only
dependencies are optional.

However, a lot has changed in the last decade! In 2006, Django was pretty
awful: we had just `removed the magic
<https://code.djangoproject.com/wiki/RemovingTheMagic>`_, but wouldn't ship
Django 1.0 for another two years. It'd be 4 years until Django supported more
than a single database, five years before it handled static files (2011), six
years before you could handle timezones properly, and eight until built-in
schema migration landed. Django in 2016 is pretty damn good compared to
what we had in 2006.

Like Django, Python packaging in 2016 is pretty damn good. We have ``pip``. It
works reliably. We have virtual environments; they're even included with Python.
Nobody even remembers the last time PyPI went down. As Glyph writes in `Python
Packaging is Good Now <https://glyph.twistedmatrix.com/2016/08/python-
packaging.html>`_:

    Python packaging is not bad any more. If you’re a developer, and you’re
    trying to create or consume Python libraries, it can be a tractable, even
    pleasant experience.

    I need to say this, because for a long time, Python’s packaging toolchain
    was … problematic. It isn’t any more, but a lot of people still seem to
    think that it is, so it’s time to set the record straight.

Indeed. It's time for Django to let go of its decade-old suspicion of the
packaging ecosystem. Python packaging is reliable and dependable, and it's time
we took full advantage of features now available.

In particular, external dependencies -- other packages specified in
``setup.py``'s ``install_requires`` argument -- should be fair game to add to
Django, when appropriate. Django core developers often duplicate effort re-
implementing  features that are available as dependencies. And, much of the
time, those external implementations are substantially better than what's
included in Django. For example:

- `passlib <https://pythonhosted.org/passlib/>`_ is a password hashing
  library that implements a large variety of password hashing algorithms.
  It's overlaps substantially with ``django.contrib.auth.hashers``, but
  Django's version has fewer features than passlib.

- Django implements its own internationalizing/localization framework, but many
  developers feel `Babel <http://babel.pocoo.org/en/latest/>`_ is a superior
  implementation.

- Django vendors a version of `six <https://pythonhosted.org/six/>`_ (as
  ``django.utils.six``). Instead of vendoring, we could use a dependency.

To be clear, this DEP isn't suggesting that we add these dependencies
specifically -- there may be good arguments both for and against each specific
example. They're offered here as examples to demonstrate ways that Django could
simplify, improve, and remove maintenance pain if we allowed dependencies.

Specification
=============

The spec is: **Django can have dependencies.**

OK, that's the easy part; the hard part is deciding *which* dependencies are
appropriate. 

Guidelines for adding new dependencies
--------------------------------------

- External dependencies should be easy to install on all the platforms that Django supports (i.e. Linux/Mac/Windows, all supported Python versions including PyPy, etc). This means that dependencies that require C extensions are probably not acceptable.
- stability
- maintainability
- "backup plan"
- requires a short DEP for a new dep, ruling by core team as usual
    - ??? accelerated mini-DEP for this?

Optional dependencies
---------------------

- optional deps are ok too, less stringent guidelines

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).

(All DEPs must include this exact copyright statement.)