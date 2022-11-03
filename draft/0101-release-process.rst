===================================================
DEP 0101: Clarify Release Process Clauses in DEP 10
===================================================

:DEP: 0101
:Author: Carlton Gibson
:Implementation Team: Carlton Gibson
:Shepherd: Mariusz Felisiak
:Status: Draft
:Type: Process
:Created: 2022-11-03
:Last-Modified: 2022-11-03

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

This is a proposal to adjust the sections of DEP 10 — the governance DEP — that
pertain to Django's release process, to bring it into line with the established
time-based release process that Django has been following since DEP 4 in 2015.

The wording in DEP 10 is in conflict with the actual release process, for which
it was not part of DEP 10's to adjust. Correcting the wording of DEP 10 to
bring it into line with the actual release policy resolves the conflict.

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
cycle for major releases — Apr - Dec - Aug, and back to Apr over a 24month
period.

Final releases are made early in the first week of the month. Major releases
have a pre-release phase, which has one alpha release, one beta, and one
release candidate.

* The release candidate comes two weeks before the final release.
* The beta comes one month before the release candidate.
* The alpha comes one month before the beta.

The exact day is left to the Releaser's discretion.

.. note::

    Factors influencing exact release day

    Factors that are considered when setting the exact release day include:
    being as close to the 1st of the month as possible, releaser availability,
    avoiding Fridays and weekends, avoiding days such as April 1st, and the
    largest international public holidays, such as New Years day.

    In general, other public holidays cannot be considered as there are too
    many internationally. Historically, though, releasers have tried to avoid
    July 4th for the sake of the US holiday there.

    This note is purely informational.

The Releaser acting as release manager for the next major version determines
the concrete dates for this schedule in the week following the previous major
version release. The reality is this falls to one of the Fellows, who by
convention alternate the release manager role for each major version.

As a matter of course regular contributors, including technical board members,
but not as a matter of obligation, review the proposed schedule in order to
spot any errors.

Within this bugfix and security releases occur at the beginning on each month
for each stable version with applied changes to be released during its
supported lifetime.

Finally, in exceptional circumstances, additional releases can be made outside
of the release schedule. Historical examples include a security release made
quickly due to a high severity vulnerability being made public, and an ad hoc
release made to correct a packaging error.

As per DEP 4, release may be held back if there are unresolved release blockers.

In their role as oversight, with the exception of security releases, the
Technical Board may vote to delay a release if they believe there is reason to
do so.

Motivation
==========

The recent discussion on widening eligibility for technical board election, and
possibly renaming to steering council to better label the role, raised various
aspects in which actual practice was diverging from the written text of DEP 10.

Some of these divergences are problems of process, which the ongoing
discussions are attempting to address. The conflict with the release process is
a problem with DEP 10, however.

That is easily resolved by bringing DEP 10 inline with the established release
process, thereby clearing up any doubts in this area, and simplifying the
remaining discussions.

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

DEP 10 concerned the dissolving of the old Django Core, the establishment or
the Technical Board, and voting around that, together with Merger, Releaser and
other related roles. Adjusting the release process was not mentioned in the
motivation or rationale for DEP 10, and it claims no relevant backwards
incompatible changes.

Likely due to focus elsewhere in DEP 10, the implicit adjustment to the release
process was not caught in review but should be corrected here. If a genuine
desire to change the release process exists, a separate DEP making that case
can be presented.

On specific points of the original DEP 10 phrasing on the release process:

* The release schedule is set entirely mechanically, as per the specification
  above. There is no determination needed, and so the requirement for the
  technical board to do so introduces artificial busy-work.
* Whilst the technical board can raise a flag if necessary, in the normal case,
  releases procede automatically, on-schedule, unless there is a specific
  reason, such as an open release blocker, for them not to. The introduction of
  the requirement for an approval vote before release introduces a risk of a
  release not occurring for a procedural failing if a vote, under DEP10's quite
  strict voting procedures, is not successfully held.
* Releasing a major version of Django is an extremely stressful activity. It
  already has many moving parts. It takes the full effort of the Releaser
  on-hand, likely with assistance from other Releasers, to do everything
  correctly. Adding the requirement to ensure that a technical board vote is
  held, when this is in-truth merely rubber-stamping the release, is an
  unnecessary extra burden.

In a utopian world where technical board members had the time and capacity to
be more directly involved in the day-to-day development of Django, these last
two points concerning the vote-to-release flow would perhaps be minimised.
That's not our world, however. Even if it were though, the correct procedure is
to not put potential pitfalls on the default path. We assume the release goes
ahead, unless there's a reason not to.

Backwards Compatibility
=======================

There is no backwards incompatibility. The change merely brings the wording of
DEP 10 into line with the established release process.

Reference Implementation
========================

A pull request with suggested changes is available for review at
`django/deps#77 <https://github.com/django/deps/pull/77>`_.

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).
