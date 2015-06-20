=======================
DEP 4: Release Schedule
=======================

:DEP: 4
:Author: Tim Graham
:Status: Final
:Type: Process
:Created: 2015-06-20

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

This DEP outlines the planned Django release schedule for the foreseeable
future. The plan is to have a new feature release every 8 months and a new
long-term support release (LTS) every 2 years. Bug fix releases will occur
approximately once per month and will be combined with security release as
needed. LTS releases are supported with security updates for 3 years.

Semantic Versioning
===================

Version numbers will follow a loose form of `semantic versioning
<http://semver.org/>`_ effective with Django 2.0 which will follow Django 1.11
(LTS).

SemVer makes it easier to see at a glance how compatible releases are with each
other. It also helps to anticipate when compatibility shims will be removed.
It's not a pure form of SemVer as each 8 month feature release will continue to
have some documented backwards incompatibilities where a deprecation path isn't
possible or not worth the cost. Also deprecations from each LTS release (X.2)
will be dropped in a non-dot-zero release (Y.1) to accommodate our policy of
keeping deprecation shims for at least two feature releases.

Starting with Django 2.0, each feature version following an LTS will bump to
the next "dot zero" version. LTS versions will thereafter always be "X.2". The
deprecation policy outlined below will make it feasible for apps to support
two LTS versions, and so third-party apps can target support for X.2 to X+1.2.

Deprecation Policy
==================

The deprecation policy is designed to ease upgrades from one LTS release to the
next and to allow third-party apps to easily support the currently supported
Django versions. The policy should make it easy to develop an app using the
latest LTS release and have it continue to work without many changes until the
next LTS. Upgrading from LTS to LTS should be easy enough if you don't use any
deprecated features when running on the older LTS.

If a feature is deprecated in feature release A.x, it will continue to work in
all A.x versions (for all versions of x) but raise warnings. Deprecated
features will be removed in the B.0 release, or B.1 for features deprecated in
the last A.x feature release to ensure deprecations are done over at least two
feature releases.

Here's an overview of when deprecated features will be dropped in Django:

* X.0
* X.1
* X.2 LTS
* Y.0: Drop deprecation shims added in X.0 and X.1.
* Y.1: Drop deprecation shims added in X.2.
* Y.2 LTS: No deprecation shims dropped (while Y.0 is no longer supported,
  third-party apps need to maintain compatibility back to X.2 LTS to ease
  LTS to LTS upgrades).
* Z.0: Drop deprecation shims added in Y.0 and Y.1.

Python support
==============

We will support a Python version up to and including the first Django LTS
release whose security support ends after security support for that version of
Python ends. For example, Python 3.3 security support ends September 2017 and
Django 1.8 LTS security support ends April 2018. Therefore Django 1.8 is the
last version to support Python 3.3.

Frequently Asked Questions and Complaints
=========================================

**Q: Will a time-based release compromise the stability of releases? Why not
release when things are ready?**

A: Release stability will be a continued priority. Releases will be delayed
(and thus support for older versions extended) as necessary if there are
major, unsolved issues.

**C: Stop breaking backwards compatibility. Many hours are wasted and money
spent all over the world because of this lack of respect for your users.**

A: The team takes backwards compatibility seriously. Sometimes it's necessary
to make such changes to continue the long-term improvement of Django. You can
help keep us honest by testing and giving feedback on prereleases. If you value
stability over new features, the deprecation policy should make it easy to use
only LTS releases and upgrade every 2-3 years.

**C: 3 years is NOT LTS at all, in the enterprise world LTS means 10 years. I
would like to have a very stable Django core that updates only on security
problems and important fixes that is supported for minimum of five years.**

A: With the exception of the Django fellow, the team is composed entirely of
volunteers with limited time. Some of us work in large enterprises, so we are
aware of these challenges. We believe that if you need support longer than 3
years, you should consider engaging a paid contractor to patch security issues
in your Django installation (much the same way that organizations provide
similar support for Python).

**Q: I'm the maintainer of a reusable application. Which Django versions should
I support?**

A: We recommend that you support the same Django versions that are supported
by the Django team. With the deprecation policy, it should be possible to
support two consecutive LTS releases and all the non-LTS versions in between
without requiring backwards-compatibility shims in your own code, as long as
your code runs warning-clean on the lower LTS, because any non-deprecated
feature in one LTS release is guaranteed to remain in place through the next
LTS release.

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (https://creativecommons.org/publicdomain/zero/1.0/deed).
