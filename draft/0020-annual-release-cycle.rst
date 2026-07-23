================================
DEP 0020: Annual Release Cycle
================================

:DEP: 0020
:Author: Carlton Gibson
:Implementation Team: Sarah Boyce, Natalia Bidart, Jacob Walls, Carlton Gibson
:Shepherd: Natalia Bidart
:Status: Draft
:Type: Process
:Created: 2026-04-24

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

This DEP proposes that Django adopt an annual feature-release cycle,
replacing the eight-monthly cycle established in `DEP 4`__.

__ https://github.com/django/deps/blob/main/final/0004-release-schedule.rst

Under the proposed schedule, Django publishes one feature release each calendar
year, in January. Each feature release is supported for three years: one year
of mainstream support, followed by two years of extended support, with the
support level changing each December. At any given time, three feature releases
are in support. The existing two-tier feature-release/LTS distinction is
retired, with every release receiving what was previously the LTS-level
commitment.

Django's version numbering moves to Calendar Versioning in the form
``YYYY.N``, so that the release year is encoded in the version itself.

The first release under this DEP is Django ``2028.0``, replacing what would
otherwise have been Django 7.0.

This DEP supersedes DEP 4 and subsumes the clarifications in `DEP 44`__.

__ https://github.com/django/deps/blob/main/final/0044-clarify-release-process.rst

Specification
=============

Release Cadence
---------------

Django will issue one feature release per calendar year.

Final feature releases will be made in approximately the second week of
January, carrying the new year's number. The exact release day remains at
the Releaser's discretion, following the factors noted in DEP 44.

Each feature release is preceded by a pre-release phase:

* An alpha release in early/mid October, following the corresponding CPython
  final release.
* A beta release in early/mid November.
* A release candidate in early/mid December.

As has been the case historically:

* Feature development is continual on Django's ``main`` development branch.
* Stable release branches are created just prior to the alpha release each
  release series. This marks the *feature freeze* for the feature release.
* In order to prepare for this release, Django's main branch will begin
  adoption of pre-release CPython versions from their pre-release phase.

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

Django will use `Calendar Versioning <https://calver.org/>`__ in the form
``YYYY.N``, where:

* ``YYYY`` is the four-digit calendar year of the feature release.
* ``N`` is a monotonically incrementing counter, starting at ``0`` for the
  feature release. Each subsequent patch release increments ``N``.

For example:

* ``2028.0`` is the feature release made in January 2028.
* ``2028.1`` is the first patch release following ``2028.0``.
* ``2028.24`` is the 24th patch release of the ``2028.x`` version, likely
  occurring late in the support window.
* ``2029.0`` is the next feature release, made in January 2029.

Version numbers remain orderable under the standard comparison rules used
by Python packaging tools. There is no third numeric component; patch
releases increment ``N``.

Support Window
--------------

Every feature release is supported for three years from its date of
release:

* **Year 1** is considered *mainstream support*, receiving fixes for security
  issues, data loss bugs, crashing bugs, major functionality bugs in
  newly introduced features, and regressions from older versions of Django.
* **Years 2 and 3** are considered *extended support*, receiving fixes for
  security issues and data loss bugs only.

The support level for a feature release changes in the December of each year,
at the point just after that month's releases are (or would be) made. At this
time, the current year's release enters extended support and the year-three
release becomes end-of-life (EOL). The new year's feature release then begins
mainstream support the following month.

This means that, bar the transition period over the new year, at any given time,
three feature releases are under support: the current release, under mainstream
support, and the two prior years' releases, under extended support.

Every release receives the same support commitment. The explicit "LTS"
label used in DEP 4 is retired; see Rationale.

Python Version Support
----------------------

At its release, each Django feature release will support three Python
versions: the two Python versions with active upstream support at the start of
the Django pre-release phase ("green"), plus the most recent Python version to
have moved to security-only status ("plus last yellow").

See the official `Status of Python versions`__ guide for reference.

__ https://devguide.python.org/versions/

In addition, the current mainstream support version of Django will adopt
support for the new version of Python that is released in the October of its
first year.

This ensures that:

* Django always supports the latest Python at the time of its release.
* The current mainstream support version always picks up support for the latest
  Python version as it is released.
* The end of Django's support window aligns closely with the end of
  upstream support for its oldest supported Python.

Given Python's release cycle, the oldest supported Python will be end-of-life
(EOL) two months before the corresponding Django version. At this point, Django
will continue to test against the then EOL Python, in order to avoid
regressions in line with the stability policy. Nonetheless, Django may decline
to address an issue affecting only the then EOL Python version, if such emerges
in the final two months of its support window.

Deprecation Policy
------------------

If a feature is deprecated in release ``A``, a deprecation warning is
raised in ``A`` and ``A+1``, and the feature is removed in ``A+2``. This
preserves the existing guarantee that a deprecated feature remains
available, with warnings, across at least two feature releases.

Because every release is supported for three years, a user on any
supported version has at least two further feature releases in which to
respond to any deprecation before it is removed.

Transition
----------

Releases up to and including Django 6.x continue on the existing schedule
under DEP 4 and DEP 44. Django 5.2 LTS and Django 6.2 LTS receive their
full advertised support windows.

The first release under this DEP is Django ``2028.0``, replacing what
would otherwise have been Django 7.0 (scheduled under the existing cycle
for December 2027). ``2028.0`` is released in January 2028 and is
supported for three years on the terms above.

Django 6.2 LTS, released April 2027, continues to receive security
support per DEP 4 alongside the first feature releases under this DEP,
with its support window concluding in April 2030.

Motivation
==========

The primary motivations for this proposal are to align better with Python's now
annual release cycle, and to close the gap between long-term support (LTS)
releases of Django. These are interlocking.

From Python 3.9, Python itself moved to an annual release schedule (`PEP 602`__).
New Python versions are released in the October each year. Each has 2 years of
full support, 3 more years of security fixes after that, before being End of
Life (EOL).

__ https://peps.python.org/pep-0602/

Python's annual release cycle has been a great success, but it fails to align
well with Django's existing 8 month release cycle, with every third release
being an long-term support (LTS) release, having three full years of security
updates.

As a concrete example, Django 4.2 LTS, which reached EOL during the preparation
of this DEP, supported five full versions of Python at the point it was EOL,
Python 3.8 to 3.12 inclusive.

Of those, Python 3.12 was released after Django 4.2 left mainstream support.
Django 4.2's status as the LTS version meant that adding Python 3.12 support
was required by the community. That's OK. We've lived with it. But it create
extra maintenance overhead that's not intended for the *extended support*
phase.

More pressingly, both Python 3.8 and Python 3.9 were end of life significantly
before Django 4.2. By the time Django 4.2 expired, Python 3.8 had been EOL for
a 18 full months. Supporting EOL versions of Python is neither good for
maintenance, nor for our users, whom we should be encouraging to upgrade onto
supported versions.

(Django 4.2 is just an example here. The Python support story shifts
symmetrically for any given Django LTS version)

By switching to an annual release cycle, Django can much better align with
Python's release schedule.

By giving every release the same *LTS* three year support window, we can remove
the gap between LTS releases.

Under the current policy, users on an LTS release do not receive most bugfixes,
which land only on the current feature release branch. Not only does this mean
that we have value that we're not able to deliver but, there are reports of
users ceasing to file issues with Django and engage in the maintenance process,
instead maintaining private patches against their LTS version.

Giving every release the same LTS support level closes this gap. Every user can
update to each feature release, receiving bugfixes (and new features) as they
do so.

Removing the gap between LTS releases also removes the relatively sudden
pressure to upgrade quickly to the new LTS, once it's finally available, before
the current one you're on becomes EOL. In theory you have a year, which sounds
plenty, but we see a `persistent pattern`__ in the download numbers for Django
where projects have failed to update from the older LTS before it reaches EOL.

__ https://buttondown.com/carlton/archive/how-we-make-decisions-in-django/#:~:text=Community%20as%20context

Removing the LTS gap encourages annual updates, allows them at any time in
the extended support window, and gives two years, rather than one, in which an
update to an equivalently supported Django is available.

At the same time, we align the update process to the official advice. In theory,
LTS-to-LTS updates are doable. In reality, we `still say`__, it’s “usually
easier to upgrade through each feature release incrementally”. By removing the
distinction there, we ease the update process for our LTS users.

__ https://docs.djangoproject.com/en/5.2/howto/upgrade-version/#:~:text=usually%20easier%20to%20upgrade%20through%20each%20feature%20release%20incrementally

Beyond these concerns, we aim to provide a simpler support story for our third-party package maintainers.

Our current recommendation is that third-party packages drop support for
everything prior to the current LTS on the release of the subsequent x.0 that
follows it. For example, the Django 6.0 release notes contain this `advice for
maintainers`__:

    Following the release of Django 6.0, we suggest that third-party app
    authors drop support for all versions of Django prior to 5.2.

__ https://docs.djangoproject.com/en/dev/releases/6.0/#third-party-library-support-for-older-versions-of-django

The reality, though, is that significant numbers of users are yet to update at
this point and there is significant pressure to maintain support for the older
LTS, well beyond the point at which we’re officially meant to have dropped it.

A rolling three-version support window (the latest release and the two prior
years') gives third-party maintainers a clear and stable FIFO queue of Django
versions to target. That it coincides with updating the Python support matrix
creates a unified, regular, and predictable cycle.

Finally, by adopting calendar versioning, to match the new release cycle, we
can clarify Django's versioning and support status, not just for users, but for
people outside the immediate Django community too.

The current ``X.Y`` numbering mimics semantic versioning despite not being
SemVer. At every x.0 release there's confusion at to why it's not a major
breaking release. The x.0, x.1, x.2 LTS cycle is opaque to people who aren't
vested in the Django community. It makes explaining Django's versioning to
stakeholders truly challenging. And without constant reference to the
`Supported Versions`__ guide, it's not feasible to know when a given version of
Django was released, or when it is supported to.

__ https://www.djangoproject.com/download/#supported-versions

Calendar versioning implies the stability and continuity, that is Django's
chief achievement as it's matured, and it makes questions obvious. When was it
released? Year. When it is end of life? Year + 3. The messaging value of this
is much more important than we're naturally inclined to credit it.

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
cost for this proposal. The bulk of Django's user base is not pushing for
faster releases, though. Rather, it's the gap between LTS releases that puts
the brake on average upgrade momentum. By removing that gap, we speed the
community as a whole.

At the same time, it's not realistic for us to offer more frequent releases,
whilst maintaining Django's support and stability guarantees. Nonetheless,
Django's main development branch is itself (remarkably) stable. Teams wanting
to be on the cutting edge have for many years deployed from the main branch.
Whilst out of scope for this DEP, it remains open for future work to improve
the messaging around testing and using Django's main development branch, and
assessing the feasibility of us providing incremental development releases as
part of the monthly release process.

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

Deprecation calendar
--------------------

A consequence of the longer release cycle is that deprecation periods
lengthen in calendar terms. Under DEP 4's eight-monthly cycle, a feature
deprecated in release ``A`` was removed approximately 16 months later in
``A+2``. Under this DEP the same ``A`` → ``A+1`` → ``A+2`` path occupies
approximately 24 months. Users gain calendar time to respond to
deprecations without any change to the policy itself.

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

The option to decline to address an issue affecting only the then EOL Python
version during the final two months of a Django version support window is there
to avoid (particularly) the Fellows and Security Team being obliged to spend
time here. It allows us to adopt the less-agressive "Plus Last Yellow" policy
without committing to fixing issues affecting only EOL Python versions. (It's a
compromise between the too-aggressive "Green Only" policy, the "rug-pull" of
dropping support for a Python version in a patch release, and not having to
spend dedicated time supporting EOL versions.)

Related work: automated upgrade tooling
---------------------------------------

Effective use of a yearly cadence benefits from good automated upgrade
tooling. The ``django-upgrade`` project provides fixers that rewrite user
code across Django versions. Formalising any role for such tooling is out
of scope for this DEP and is suitable material for a separate proposal.

Backwards Compatibility
=======================

API stability commitments under this DEP are preserved: deprecated
features continue to warn for at least two feature releases before
removal, and security support extends for three years from each release.

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
  effect at a clearly signposted release (``2028.0``), maintainers have
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
