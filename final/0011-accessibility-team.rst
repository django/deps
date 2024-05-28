==========================
DEP 11: Accessibility Team
==========================

:DEP: 11
:Author: Tom Carrick
:Implementation Team: Tom Carrick, Thibaud Colas, Sarah Abderemane, Tushar Gupta, Saptak Sengupta, Eli Rosselli, others to be determined.
:Shepherd: Carlton Gibson
:Status: Final
:Type: Process
:Created: 2020-06-29
:Last-Modified: 2023-10-23

.. contents:: Table of Contents
  :depth: 3
  :local:

Abstract
========

This DEP proposes the formation of an Accessibility Team to encourage projects
maintained by the Django Software Foundation to be accessible to as many
people as possible, particularly those with disabilities that make using the
web more difficult.

Specification
=============

The Accessibility Team (informally, a11y team) shall be formed.

Membership
----------

The team shall not have a fixed size, but instead will grow and shrink
organically as members choose to leave, and when new members are deemed to be
required by the rest of the team. Membership of the team works similarly to the
`Code of Conduct Committee <https://github.com/django/code-of-conduct/blob/main/membership.md>`_.
New members shall be chosen from a list of volunteers, or if there is a lack
of volunteers, an advertisement will be published on the Django website.
Priority will be given to volunteers who, in no particular order:

- Have disabilities that make using the web and/or web development more
  difficult.
- Have relevant, positive contributions or expertise in the field.
- Have a record of contributing to Django.

Members shall remain in the team for a fixed-term of 9 months, after which
they must opt-in to remain on the team for another term. They may also leave
on their own volition at any time and for any reason. Membership will also be
terminated by:

- Becoming disqualified due to actions taken by the Code of Conduct committee
  of the Django Software Foundation.

- A vote of the Technical Board, or full consensus of the rest of the
  Accessibility Team, if the team is considered too large, the person is not
  making positive contributions, or any other sound reason.

Responsibilities
----------------

The remit of the Accessibility Team shall include all user-facing components
of projects maintained by the Django Software Foundation. This includes but is
not limited to:

- User-facing parts of Django, such as default HTML output in forms and such,
  and the Django admin and its default theme, HTML, and UI components.

- All websites and other software projects maintained by the DSF, such as the
  Django website, projects' documentation, Django Snippets, the issue tracker, etc.

The responsibilities of the Accessibility Team are expected to change over
time, and are to be decided by consensus of the team, with input from the
Technical Board as required. To begin, several areas have been identified:

- Deciding on any relevant accessibility guidelines to follow, such as WCAG,
  and at which conformance level.

- Implementing automated testing to catch issues, working with the ops
  team as needed to integrate this into CI processes.

- Coordinating regular manual accessibility audits on all relevant projects.

- Coordinating the fixing of accessibility issues and the improvement of the
  accessibility in general in Django and associated projects.

- Writing and maintaining documentation relating to accessibility, such as
  a statement of commitment to accessibility issues, and contribution
  guidelines.

- Reviewing accessibility fixes, improvements and other tickets that may affect
  accessibility of any relevant project.

To aid in reviewing, the Accessibility Team members shall be added to a team
in the GitHub organization with read access to relevant repositories, so that
they may be requested to review pull requests, at the discretion of the author,
reviewer, or other party.

Many of these duties can be undertaken by any contributor, not only by the
Accessibility Team, however the Accessibility Team exists to coordinate this
work and to step in where contributors are not available and support those who
lack the knowledge to do so themselves.

Motivation
==========

Accessible websites are not technically difficult to create, but accessibility
is often overlooked when developing features. Django is no exception to this,
and given Django's commitment to diversity and inclusion, the lack of
accessibility in many parts of Django falls short of an acceptable standard.

Improving accessibility also has a tendency to improve the experience of other
users. This is called the
`curb cut effect <https://alexwlchan.net/2019/01/monki-gras-the-curb-cut-effect/>`_
While this is mostly noted in the real world, the web also experiences this
effect. For example, keyboard shortcuts are used to allow keyboard-only users
navigate a site more efficiently, but this positive benefit affects everyone,
not just the physically disabled.

The Django admin currently exhibits many accessibility issues, such as forms
fields missing labels, low color contrast, and a lacklustre keyboard-only
experience among other issues. Other parts of the project have problems such
as non-semantic HTML generated by forms. Further problems exist on other sites
maintained by the DSF, such as the
`Django website <https://www.djangoproject.com/>`__,
`Django Snippets <https://djangosnippets.org/>`_, and others.

Rationale
=========

An alternative is to go on as usual, leaving accessibility in the hands of
individual contributors when writing and reviewing code. However, given the
accessibility issues that exist in the Django admin and on the
`Django website <https://www.djangoproject.com/>`__, this doesn't seem to be
enough.

Another option is to implement some basic standards, such as conforming to WCAG
and setting up CI tests. This approach is better than nothing but it
lacks a clear process for deciding on these. Ongoing maintenance would also be
necessary to keep any CI or other tooling up to date with Django's code, along
with manual audits - as
`automatic processes cannot find every issue <https://alphagov.github.io/accessibility-tool-audit/>`_
- and these could be easily forgotten.

Resources
=========

- `Diverse Abilities and Barriers (W3C)
  <https://www.w3.org/WAI/people-use-web/abilities-barriers/>`_
- `Accessibility, Usability, and Inclusion (W3C)
  <https://www.w3.org/WAI/fundamentals/accessibility-usability-inclusion/>`_
- `Web Content Accessibility Guidelines (WCAG) Overview
  <https://www.w3.org/WAI/standards-guidelines/wcag/>`_
- `Authoring Tools Accessibility Guidelines (ATAG) 2.0
  <https://www.w3.org/TR/ATAG20/>`_

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).
