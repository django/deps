==================================
DEP 0007: Official Django Projects
==================================

:DEP: 0007
:Author: Andrew Godwin
:Implementation Team: Andrew Godwin
:Shepherd: Andrew Godwin
:Status: Draft
:Type: Process
:Created: 2016-06-01
:Last-Modified: 2016-06-08

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

Define a process for adopting and managing projects under the Django name
and organisation that are not the core ``django`` repository and documentation.

Motivation
==========

With the growing popularity of Django and the increasing number of projects
living outside of the core repository that are nonetheless central to the
Django community and mission, and a desire to not grow the size of the main
Django repository with optional or extra code, it becomes apparent that there
is a need for "official" Django projects that exist outside that repository
but still are part of the Django organisation and management structure.

Leaving these projects outside means they're often limited in their ability
to maintain and grow the project based on the few people working on the
project directly, and becoming an official project will benefit them with
increased exposure, existing project infrastructure and process (like the
security reporting process), and lend them greater credibility for larger,
more risk-averse companies and projects who aren't sure what option to pick.

It also helps Django as a project overall. Adopting external projects that
solve problems and add features that the core Django project doesn't have
helps us as a project:

* It shows off Django-related features that people would otherwise miss.
* It aids new Django developers by highlighting projects that they might
  otherwise overlook.
* It acts as a useful conduit to get people contributing to Django without
  having to tackle (large, difficult) issues on the core project.

Rationale
=========

The goal of this proposed process is to enable a system where projects can
be adopted and become official Django projects, but making sure it's not
done prematurely (and thus stifling alternative approaches), and that it
doesn't tie development to the release cadence and style of Django core
releases too directly.

That said, the Django name has gained a level of trust and respect over the
years from our community and users, and so to become an official Django
project a level of quality, commitment, and security must be met, and this
process tries to ensure those are accounted for.

Finally, projects and maintainers move on, and so this document tries to
outline a process where projects can be deprecated or handed off between
maintainers in a way that's transparent and allows Django as a whole to have
a clear idea of the status of a project at any time.

Adoption Process
================

An external project will exist in one of three phases of its lifecycle -
adoption, where it's being discussed for inclusion in the Django project
overall, maintenance, where it's part of the project and releasing new
versions and applying bugfixes, and deprecation, where it's either lost all
maintainers or is no longer needed, and is gently removed from the overall
project.

Adopting a project to be an official Django project consists of a number
of phases, which are:

1. `Pre-proposal`_ — a project looks like it may be worth adopting into Django
   officially and initial discussions about the potential are had.

2. `Forming a team`_ — the project gathers together an official maintenance
   team including a core shepherd.

3. `Discussion and debate`_ — the community discusses the project and the
   merits of making it an official Django project.

4. `Review & Resolution`_ — the project proposal is reviewed by the Technical
   Board and a decision made if it should be adopted.

5. `Adoption`_ — the project is officially adopted and moved into Django
   ownership and maintenance.

Pre-proposal
------------

The adoption process begins when a project, new or old, looks like it might
benefit greatly from adoption as an official Django project, and that Django
as an overall ecosystem might benefit from the project being made official.

Initial discussions should be held on mailing lists and other venues to
solicit feedback from the community and work out if there is rough agreement
that the project is a good thing for Django to adopt, particularly focusing
on any alternative approaches to the same problem and the relative merits
of them, including code design, scalability, alignment with existing Django
design and philosophy, and having an available development and maintenance team.

Notably, it does not need to be a maintainer of the existing project that
starts this process, but a proposed project will need an implementation team
willing to work with it once it is adopted to make it past the next step. If it
is not the existing maintenance team, they should still be in agreement (if the
project is not abandoned).

To even be considered for adoption into Django, the project must have a
compatible open-source license, ideally the BSD three-clause license which
Django itself is under.

Forming a team
--------------

Once the project looks like it might be a good candidate for an official
Django project, a team must be formed to look after the adoption process,
including:

Maintenance Team
    One or more people who are committed to maintaining the project once it
    is part of Django. A project must have an active and willing maintenance
    team to be adopted, and at least one member of the team must be willing and
    able to respond to security issues filed against the project in a timely
    manner.

Shepherd
    The **Shepherd** is the Core Developer who will be the primary point of
    contact for the project with the Core Team in Django, who will liase with
    the Technical Board for the final vote, and who will assist in moving and
    running the project under official Django ownership and infrastructure.
    They can also be part of the Maintenance Team.

The maintenance team for the adopted project may be different from that of the
project pre-adoption, but a project should not be adopted against the wish of
the original maintainers; instead, a team change would likely happen if the
project was abandoned or the existing maintainers wished to step down, but the
project is considered crucial enough to Django that it should be adopted.

It is important that the maintenance team are aware of the requirements
imposed on official projects in `Ongoing Maintenance`_ below; if a project
falls out of maintenance, it may have to be retired.

Discussion and debate
---------------------

Once a team is assembled, the project will be taken for full discussion on
mailing lists and other archived public fora, and the Shepherd and Maintenance
Team will be responsible for guiding the discussion, making sure it does not
get too long-winded or descend into "bike-shedding", and for collating the
arguments for and against into a single document with linked references
for use during the review phase.

The discussion is not expected to reach a consensus, though if it does that
makes the review phase much easier; instead, it is meant for the community to
discuss the pros and cons of adoption (the cons likely being alternative
approaches to the same problem, or concerns that adoption will harm the project
or Django), and make sure all opinions are heard.

Of particular note should be the presence of good documentation for the
project; without this, it may be hard to discuss what it is or means. Projects
with no documentation should likely not be considered for discussion before
at least some documentation is written to anchor the discussion.

The Shepherd should call an end to discussions after a reasonable time period;
there is no requirement to wait until all discussions have "finished" before
moving on (as this may take a very long time); instead, they should move
on when they are confident that all viewpoints have been heard and collated.
The Technical Board may refuse the adoption if they think the project was moved
onto the next phase too quickly.

Review & Resolution
-------------------

Once a project has been discussed and the discussion collated by the
Maintenance Team and the Shepherd, it is moved onto review and decision by
the Technical Board. The Shepherd will submit the project, the list of people
signed up for the Maintenance Team, and the collated arguments to the
Technical Board for decision.

The Technical Board are the final authority for deciding on adopting a project
or not. They may choose to rule on the project as a team, or they
may designate one or more board members to review and decide.

The Technical Board should consider:

* If the project's adoption would benefit Django.
* If by adopting they are crowding out other, potentially superior solutions.
* If the maintenance team is sufficient to ensure the project will
  be maintained properly once adopted.
* If the adoption of the project would place undue stress on the existing core team.
* If adopting the project projects the right image and message about what Django is.

They should err on the side of denial if there is some controversy or
heavy disagreement in the community about the adoption; a project can always
come back for another attempt at adoption later, but adopting it prematurely
is very hard to undo.

Once the decision is made, the Technical Board will inform the Shepherd about
the decision, and a public announcement will be made about either the success
or failure of the project's adoption proposal.

Adoption
--------

If the project's adoption proposal is sucessful, then steps should be taken
to make it an official Django project:

* The repository should be moved under the "django" organization on GitHub,
  and the Shepherd given administrative access to it so they can hand out
  commit and other access to the Maintenance Team as needed.

* The top-level README of the project should be updated to officially list the
  Shepherd and Maintenance Team, as well as details about Django's security
  policy.

* References to the project should be added in the official Django
  documentation where sensible, as well as other changes made to ensure it's
  discoverable.

Ongoing Maintenance
===================

Once a project is an official Django project, it needs to maintain a certain
quality that comes with the Django name. In particular, an official Django
project must maintain the following things:

* An up-to-date list of maintainers and a current core Shepherd, listed in
  the top-level README file.

* Tracking and response to security issues on par with Django's official
  security policy.

* Release notes for each major release with backwards-incompatability sections
  and information about which versions of Django they support.

* Compatability with the current release and current LTS release of Django,
  within a month of the Django release coming out (LTS compatability may be
  with an older but still maintained version)

If any of these requirements does not continue to be true, effort should be
made to find new maintainers or a new Shepherd to bring the project up to
par; if it does not get there after two months, it should be retired according
to the section below.

Official projects do not have to maintain a similar backwards-compatability
policy to the core Django repository, nor are they subject to the same
contribution patterns and guidelines as the core repository; how these work are
up to the Maintenance Team.

Maintainers are free to resign from their position at any time; the team
should ideally have more than one member so that this does not put the
project at risk of retirement.

Maintainers or people with commit access on an official Django project do not
have to be core Django memebers, nor do they become core members by taking
those positions, but they should be very strongly considered as candidates for
the Core Team if they are not already.

The main project documentation does not have to be hosted inside the main
Django documentation, but should be under an official Django domain
if possible, and link back to with the main Django documentation where it makes
sense.

Retiring Projects
=================

If a project falls out of active maintenance, or has outlived its usefulness
(maybe the functionality was rolled into the core Django repository), it should
be retired as an official signal that it is no longer maintained.

Retirement involves the following steps:

* Modifying the README file on the repository to remove the maintainer lists
  and display prominently at the top that it is no longer active. The
  repository will remain in-place under the Django organisation.

* Remove the project from all official Django documentation.

* Publicly announce the retirement of the project on official mailing lists,

* Modify the PyPI (and other) package entries to show that it is no longer
  maintained.

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).
