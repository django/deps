================================
DEP 0020: Annual Release Cycle
================================

:DEP: 0020
:Author: Carlton Gibson
:Implementation Team: TBD
:Shepherd: TBD
:Status: Draft
:Type: Process
:Created: 2026-04-24

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

This DEP proposes that Django adopt an annual release cycle for major
versions, replacing the eight-monthly cycle established in `DEP 4`__.

__ https://github.com/django/deps/blob/main/final/0004-release-schedule.rst

Under the proposed schedule, one major version of Django is released each
calendar year, in January, and is supported for three years: one year of
bugfix and security releases, followed by two years of security releases
only. At any given time, three major versions are in support. The existing
two-tier feature-release/LTS distinction is retired, with every release
receiving what was previously the LTS-level commitment.

Django's version numbering moves to Calendar Versioning in the form
``YYYY.N``, so that the release year is encoded in the version itself.

The first release under this DEP is Django ``2028.1``, replacing what would
otherwise have been Django 7.0.

This DEP supersedes DEP 4 and subsumes the clarifications in `DEP 44`__.

__ https://github.com/django/deps/blob/main/final/0044-clarify-release-process.rst

Specification
=============

Release Cadence
---------------

Django will issue one major release per calendar year.

Final major releases will be made in approximately the second week of
January, carrying the new year's number. The exact release day remains at
the Releaser's discretion, following the factors noted in DEP 44.

Each major release is preceded by a pre-release phase:

* An alpha release in early October, following the corresponding CPython
  final release.
* A beta release approximately four weeks before the release candidate.
* A release candidate approximately two weeks before the final release.

Bugfix and security releases continue to be made at the beginning of each
month for each supported stable version, as per DEP 4 and DEP 44. In
exceptional circumstances, additional releases may be made outside the
schedule (for example, for a high-severity security issue or a packaging
error).

As per DEP 4, non-security releases may be held back if there are
unresolved release blockers. The Steering Council may vote to delay a
non-security release if it believes there is reason to do so.

Versioning
----------

Django will use Calendar Versioning in the form ``YYYY.N``, where:

* ``YYYY`` is the four-digit calendar year of the major release.
* ``N`` is a monotonically incrementing counter within that year, starting
  at ``1`` for the major release. Each subsequent bugfix release
  increments ``N``.

For example:

* ``2028.1`` is the major release made in January 2028.
* ``2028.2`` is the first bugfix release following ``2028.1``.
* ``2029.1`` is the next major release, made in January 2029.

Version numbers remain orderable under the standard comparison rules used
by Python packaging tools. No third number is used; there is no separate
"patch" component.

Support Window
--------------

Every major release is supported for three years from its date of release:

* **Year 1**: bugfix and security releases.
* **Years 2 and 3**: security releases only.

At any given time, three major versions are under support: the current
release and the two prior years' releases. On the release of
``YYYY.1``, bugfix support for ``(YYYY-1).1`` ends, and security support
for ``(YYYY-3).1`` ends.

Every release receives the same support commitment. The explicit "LTS"
label used in DEP 4 is retired; see Rationale.

Python Version Support
----------------------

Each Django major release supports three Python versions: the two Python
versions with active upstream support at the start of the Django
pre-release phase ("green"), plus the most recent Python version to have
moved to security-only or end-of-life status ("plus last yellow").

This ensures that:

* Django always supports the latest Python at the time of its release.
* The end of Django's support window aligns closely with the end of
  upstream support for its oldest supported Python.

Deprecation Policy
------------------

If a feature is deprecated in release ``A``, a deprecation warning is
raised in ``A`` and ``A+1``, and the feature is removed in ``A+2``. This
preserves the existing guarantee that a deprecated feature remains
available, with warnings, across at least two major releases.

Because every release is supported for three years, a user on any
supported version has at least two further major releases in which to
respond to any deprecation before it is removed.

Transition
----------

Releases up to and including Django 6.x continue on the existing schedule
under DEP 4 and DEP 44. Django 5.2 LTS and Django 6.2 LTS receive their
full advertised support windows.

The first release under this DEP is Django ``2028.1``, replacing what
would otherwise have been Django 7.0 (scheduled under the existing cycle
for December 2027). ``2028.1`` is released in January 2028 and is
supported for three years on the terms above.

Motivation
==========

*Outline — WIP to be expanded*

* **Alignment with Python's annual release cycle.** Python has released
  annually since Python 3.9. Django's eight-month cycle is continually
  misaligned with Python's, complicating Python support decisions and
  increasing the matrix of supported interpreters.

* **Removing the gap between LTS cycles.** Under the current policy, users
  on an LTS release do not receive most bugfixes, which land only on the
  current feature release. There are reports of users ceasing to file
  issues with Django and instead maintaining private patches against
  their LTS version. Making every release an LTS closes this gap: every
  supported user receives bugfixes for a full year.

* **Simpler support story for third-party packages.** A rolling
  three-version support window (the latest release and the two prior
  years') gives third-party maintainers a clear and stable FIFO queue of
  Django versions to target. Today, the overlap between the end-of-life
  of an old LTS and the active life of new feature releases puts
  maintainers under pressure to support more versions at once, for
  longer.

* **Version and timing clarity (secondary).** The present ``X.Y``
  numbering mimics semantic versioning despite not being semver, and the
  numbers carry no information about when a release was made or how
  current it is. ``YYYY.N`` encodes both, and makes Django's actual
  stability and upgrade story easier to communicate. This is a genuine
  improvement but is not the primary driver for this DEP.

Rationale
=========

Annual cycle
------------

Python's move to annual releases has made the existing eight-month cycle
progressively harder to reason about. An annual cycle aligns Django's
pre-release phase with the CPython release in October, giving Django a
predictable window in which to validate against a newly released Python
before Django's own final release in January.

A January final release, carrying the new year's number, gives a
"New Year, not Last Year" feel to each release and avoids the December
holiday period for both the Releaser and users evaluating upgrades.

Annual releases are (of course) slower than eight monthly ones, and that is a
cost for this proposal. At this stage in Django's lifecycle, and given its
strong stability guarantees, the motivating factors for this DEP make it one
worth paying.

Every release as LTS
--------------------

The current two-tier system has a well-documented failure mode: the
backport policy means that users on an LTS receive only a small subset of
fixes, while users who stay current receive bugfixes but face more
frequent upgrades. Collapsing this into a single tier — every release
supported for three years — removes the failure mode without reducing the
commitment offered to any user.

The explicit "LTS" label is retired in this DEP on the grounds that every
release now carries the commitment that label previously denoted. It
remains the responsibility of the Marketing Working Group, the
djangoproject.com site, and the Django documentation to communicate the
length and stability of the three-year support window clearly — both to
existing users and to stakeholders evaluating Django against other
frameworks. (Retaining the "LTS" label on every release, as an
always-applied marker rather than a distinguishing one, remains a viable
option if the working group and documentation editors find it useful.)

Calendar Versioning: ``YYYY.N``
-------------------------------

Calendar Versioning is proposed in the four-digit form ``YYYY.N``.

The two-digit form ``YY.N`` was considered and remains a possibility. It
is more concise and follows the well-known Ubuntu pattern (``YY.MM``).
Against it: short year numbers continue to resemble semver major numbers
and so may perpetuate the confusion this DEP hopes to reduce. CPython's
`PEP 2026`__ proposed a similar year-based scheme for Python itself and
was rejected; that discussion surfaces considerations (version
comparisons, tooling expectations, reader cognition) that apply to Django
as well, and the four-digit form is the simpler response to most of them.

__ https://peps.python.org/pep-2026/

A prior `Django Forum thread`__ discussed adjusting Django's versioning
in isolation and did not reach consensus. This DEP reframes the question:
the primary change is the release cycle and support model, and the
versioning change follows from, and reinforces, that primary change. The
versioning scheme is presented here as part of a coherent whole rather
than as a standalone adjustment.

__ https://forum.djangoproject.com/t/should-we-adjust-djangos-versioning-to-use-a-form-of-calver/42811

Python support: "Plus Last Yellow"
----------------------------------

Of the two Python support policies sketched in the preliminary
discussion — "Green Only" (the two currently supported Python versions)
and "Plus Last Yellow" (those two plus the most recent end-of-life or
security-only version) — this DEP selects "Plus Last Yellow".

"Plus Last Yellow" is the less aggressive of the two. It gives users one
additional Python version per Django release, smoothing the Python
upgrade path and remaining more compatible with the support windows of
common Linux distributions, where a stable release typically tracks a
specific Python version for around three years.

Third-party package maintainers, particularly those of newer or
still-evolving packages, may reasonably adopt a "Green Only" Python
support policy for their own releases, in order to reduce their own
maintenance burden, without this being in conflict with Django's wider
policy.

Related work: automated upgrade tooling
---------------------------------------

Effective use of a yearly cadence benefits from good automated upgrade
tooling. The ``django-upgrade`` project provides fixers that rewrite user
code across Django versions. Formalising any role for such tooling is out
of scope for this DEP and is suitable material for a separate proposal.

Backwards Compatibility
=======================

API stability commitments under this DEP are preserved: deprecated
features continue to warn for at least two major releases before removal,
and security support extends for three years from each release.

The main compatibility impacts are on tooling and ecosystem expectations
rather than on Django's Python API:

* **Version string format.** ``YYYY.N`` is a new shape for Django's
  version number. Code that parses or compares Django versions using
  standard packaging tools (``packaging.version``, ``pip``'s resolver,
  and similar) continues to work, since ``YYYY.N`` remains a
  PEP 440-compliant, orderable version. Code that relies on ``X.Y``
  having a bounded major component, or that uses ad hoc string parsing,
  will need updating.

* **The "LTS" label.** External resources (hosting providers, tutorials,
  books, third-party packages) that refer to "the Django LTS" will need
  to be updated to reflect that every release is long-term supported.
  The Marketing Working Group and the documentation are expected to lead
  on this communication.

* **Release tooling and schedules.** Internal release tooling, the
  ``internals/release-process/`` documentation, and the release schedule
  published on djangoproject.com all need to be updated to reflect the
  new cadence and numbering.

* **Third-party package metadata.** ``Framework :: Django :: X.Y``
  trove classifiers, tox environments, and CI matrices in the wider
  ecosystem will need to be adjusted. Because the transition takes
  effect at a clearly signposted release (``2028.1``), maintainers have
  advance notice.

No change is proposed to the support commitments already made for Django
5.2 LTS or Django 6.2 LTS under the existing schedule.

References to, for example, Steering Council terms that are grounded in LTS
cycles will need to be updated to simply state two-years, or as appropriate.

Reference Implementation
========================

There is no reference implementation at the time of writing. Adoption of
this DEP requires changes including:

* Updating the release schedule at
  ``docs/internals/release-process.txt`` in the Django repository.
* Updating the release checklist at
  ``docs/internals/howto-release-django.txt``.
* Updating release tooling and version-string handling in
  ``django/__init__.py`` and related locations.
* Updating the download and "supported versions" pages on
  djangoproject.com.
* Communicating the change via the Django blog and the Marketing
  Working Group.

Copyright
=========

This document has been placed in the public domain per the Creative
Commons CC0 1.0 Universal license
(https://creativecommons.org/publicdomain/zero/1.0/deed).
