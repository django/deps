=================================
DEP 0044: Clarify Release Process
=================================

:DEP: 0044
:Author: Carlton Gibson
:Implementation Team: Carlton Gibson
:Shepherd: Mariusz Felisiak
:Status: Draft
:Type: Process
:Created: 2022-11-03

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

This DEP clarifies Django's time-based release process, providing additional
information to the 2015 DEP 4 that established the release process.

Specification
=============

Django has a time-based release schedule, as specified in `DEP 4`__ and the `Release
Process`__ page of the Django documentation. Supplemental information is available
in the `How is Django Formed?`__ release process checklist, and the `2015 post on
the Django blog announcing the then new release schedule`__.

__ https://github.com/django/deps/blob/main/final/0004-release-schedule.rst
__ https://docs.djangoproject.com/en/dev/internals/release-process/
__ https://docs.djangoproject.com/en/dev/internals/howto-release-django/
__ https://www.djangoproject.com/weblog/2015/jun/25/roadmap/

Scheduling is entirely mechanical. Django has a fixed eight monthly release
cycle for major releases: April, December, August, and back to April over a 24
month period.

Final releases are made early in the first week of the month. Major releases
have a pre-release phase, which has one alpha release, one beta, and one
release candidate.

* The release candidate comes two weeks before the final release.
* The beta comes four weeks before the release candidate.
* The alpha comes five weeks before the beta.

The exact day is left to the Releaser's discretion.

.. note::

    Factors influencing exact release day

    Factors that are considered when setting the exact release day include:
    being as close to the 1st of the month as possible, releaser availability,
    avoiding Fridays and weekends, avoiding April 1st (April Fool’s Day), and the
    largest international public holidays, such as New Year's Day.

    In general, other public holidays cannot be considered as there are too
    many internationally. Historically, though, releasers have tried to avoid
    July 4th for the sake of the US holiday there.

    This note is purely informational.

The Releaser acting as release manager for the next major version determines
the concrete dates for this schedule in the week following the previous major
version release. The reality is this falls to one of the Fellows, who by
convention alternate the release manager role for each major version.

As a matter of course, but not as a matter of obligation, regular contributors,
including Steering Council members, review the proposed schedule in order to
spot any problems.

Within this, bugfix and security releases occur at the beginning of each month
for each stable version with applied changes to be released during its
supported lifetime.

Finally, in exceptional circumstances, additional releases can be made outside
of the release schedule. Historical examples include a security release made
quickly due to a high severity vulnerability being made public, and an ad hoc
release made to correct a packaging error.

As per DEP 4, non-security releases may be held back if there are unresolved
release blockers.

In their role as oversight, with the exception of security releases, the
Steering Council may vote to delay a release if they believe there is reason to
do so.

Motivation
==========

The recent discussion on widening eligibility for Steering Council election, and
possibly renaming to steering council to better label the role, raised various
aspects in which actual practice was diverging from the written text of DEP 10 — the governance DEP.

Some of these divergences are problems of process, which the ongoing
discussions are attempting to address. The conflict with the release process is
a problem with DEP 10, however.

That is easily resolved by clarifying the release process here, and bringing DEP 10 inline with that, by defering to this DEP.

Once noticed, it's not sustainable to have Django's governance DEP in conflict
with the actual release process.

Rationale
=========

Since its introduction in 2015, the time-based release process, and the manner
in which it ties into the LTS, API stability, and deprecation policies has been
an unmitigated success. It has brought key benefits of predictability and ease
of updates.

Any change to Django's release process would require a full DEP of its own and
it was not part of DEP 10's scope to address this.

DEP 10 concerned the dissolving of the old Django Core, the establishment of
the Steering Council, and voting around that, together with Merger, Releaser and
other related roles. Adjusting the release process was not mentioned in the
motivation or rationale for DEP 10, and it claims no relevant backwards
incompatible changes.

Likely due to focus elsewhere in DEP 10, the implicit adjustment to the release
process was not caught in review but should be corrected here. If a genuine
desire to change the release process exists, a separate DEP making that case
can be presented.

On the specific points of the original DEP 10 phrasing on the release process,
the release schedule is set entirely mechanically, as per the specification
above. There is no determination needed, and so the requirement for the
Steering Council to do so introduces artificial busy-work.

Backwards Compatibility
=======================

There is no backwards incompatibility. The change merely brings the wording of
DEP 10 into line with the established release process.

Reference Implementation
========================

This DEP is its own implementation. The PR adding it will make necessary
changes to DEP 10.

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).
