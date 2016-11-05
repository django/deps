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
:Last-Modified: 2016-11-05

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

This DEP outlines Django's policy on external dependencies (e.g. other Python
packages required to run Django). It supersedes Django's previous, unwritten
policy of "no external dependencies allowed."

In a nutshell, the policy is that adding a new external dependency should be
treated similarly to adding a major new feature to Django: it requires a DEP,
demonstration that the dependency is needed, rough consensus among the
community and core team that the chosen dependency, and a final decision by
the Technical Board.

The rest of this document explains the guidelines and process for adding new
dependencies, as well as the background and motivation about why this policy was
created.

Specification
=============

The spec is: **Django can have dependencies.**

OK, that's the easy part; the hard part is deciding *which* dependencies are
appropriate. This DEP does not lay out a hard and fast set of rules;
a single set of rules is unlikely to cover all cases. Instead, it defines
a set of guidelines and a process for considering external dependencies.

Guidelines for adding new dependencies
--------------------------------------

In a nutshell, external dependencies need to be at a similar level of maturity
as Django itself. We define "maturity" as:

- **Stable** - Django's pretty solid at this point: it's well-tested,
  production-proven, and relatively bug-free. All software has bugs, of course --
  Django has 1,200 open issues as November 2016 -- but Django is, roughly
  speaking, free of really critical bugs (crashers, data-loss, security issues,
  etc). Dependencies need to be at a similar level of quality: code with serious
  issues that wouldn't make it into Django shouldn't be accepted as a dependency,
  either.

- **Maintained** - if we discover bugs in a dependency, we need to be fairly 
  confident that they'll be fixed quickly.

- **Takes security seriously** - we should be confident that if we or our users
  discover vulnerabilities in a dependency that the dependency authors will
  respond to those vulnerabilities in coordination with us. This means they
  should have a vulnerability disclosure policy, security-specific contacts,
  and a history of taking vulnerabilities seriously.

- **Works on all the same platforms as Django does** - Linux, Mac, Windows, 
  and all supported Python versions (including PyPy). This probably means that 
  dependencies that require C extensions are probably not acceptable [1]_. 

- **Backwards compatible** in minor releases. We should be able to specify as
  wide a range of required versions as possible so that releases of Django
  are de-coupled (as much as possible) from dependencies. Generally, we'll
  want to specify dependencies as ``foo>=1.0,<2.0``, and be confident that
  point-releases of ``foo`` won't break Django. 

Again, these are guidelines. At the end of the day, the criteria comes down to
"would we include this code in Django?" The Tech Board has the final call.

.. [1] Note the "probably" there. It is, in principle, possible to distribute 
       C extensions in a way that no longer requires a complier -- platform-
       specific Wheels,  statically-linked dependencies, testing explicitly for
       PyPy support, etc. However, this would still leave out people who use
       OSes that don't have Wheel support (BSDs) or folks who compile their own
       Pythons, but that may be OK given that Django doesn't really test on
       these platforms either. All that to say that we shouldn't 100% rule out
       dependencies with C extensions, but they will face a higher bar.

Process
-------

There's no process for adding a dependency on its own, since the whole point of
a new dependency is to introduce new feature (it would be silly to add a new
dependency without using it in some way). So, new dependencies get proposed as
part of a larger feature DEP. For example, you wouldn't propose a  "Start
depending on Babel" DEP; you'd propose a "Improve i18n/l10n framework" DEP that
includes introducing Babel as part of the DEP.

DEPs that introduce new dependencies will need a "Dependencies" section that
answers a few questions:

- What's the dependency? Why should we use it over re-inventing this
  particular wheel [2]_?

- Does the package meet the maturity bar laid out above? If there are 
  any maturity risks -- for example, if the project only has a single 
  maintainer -- that should be identified so we can do a cost/benefit
  analysis.

- What version will we depend on? In general, we'd like to depend on a
  wide range of versions (e.g. ``foo>1.0,<2.0``) so we can avoid tightly
  coupling dependency releases to Django releases. But this may differ
  from package to package, so the DEP should explain it closely.

.. [2] Pun completely intended.

From there, the rest of the DEP process proceeds as usual. When the Tech Board
evaluates the DEP for acceptance, it will include an evaluation of dependencies
following the guidelines above.

Re-evaluating dependencies
--------------------------

During each minor release cycle -- and especially before LTS releases -- the
core team should re-evaluate all existing dependencies. If some dependency is
starting regress on the maturity front (particularly if it has become
unmaintained), we want to identify it early and start looking for backup plans.
This might mean removing the dependency, taking over maintenance ourselves, 
looking for funding to pay new maintainers, etc.

Background and Motivation
=========================

When Django was first being developed, Python packaging was in its infancy.  By
the time of Django's first release (July 2005), the shape of Python's modern
packaging infrastructure was starting to emerge [3]_: PyPI had been around for a
couple of years (since 2003), and in 2005 Setuptools added the ``easy_install``
command, allowing users to automatically download and install packages from
PyPI, including dependencies.

.. [3] For more information on the early history of Python packaging, see
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
Django, when appropriate. Django core developers often duplicate effort
re-implementing  features that are available as dependencies. And, much of the
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

- Much of Django's core HTTP/WSGI handling overlaps with utilities provided by
  `Werkzeug <http://werkzeug.pocoo.org/>`_, the base underlying Flask and more.
  If Django reimplemented its core HTTP/WSGI handling, we could share
  maintenance burden with the Werkzeug/Flask maintainers while starting to
  offer more opportunities for interoperability.

To be clear, this DEP isn't suggesting that we add these dependencies
specifically -- there may be good arguments both for and against each specific
example. They're offered here as examples to of the types of options that open
up once we start to allow external dependencies.

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).

(All DEPs must include this exact copyright statement.)
