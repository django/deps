=====================================================
DEP 0019: Technical governance for the Django project
=====================================================

:DEP: 0019
:Author: Carlton Gibson, Emma Delescolle, Frank Wiles, Lily Foote,
  Tim Schilling
:Implementation Team: Carlton Gibson, Emma Delescolle, Frank Wiles,
  Lily Foote, Tim Schilling
:Shepherd: TBD
:Status: Draft
:Type: Process
:Created: 2026-04-16

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

This defines the technical governance for the Django project. It describes
how Django is developed, how decisions are made, the organization of the
community from a technical perspective and how these are changed.

Terminology
===========

The following terms are used in this document to refer to types of
changes made to Django's codebase:

* "Minor Change" means fixing a bug in, or adding a new feature to,
  Django of a scope small enough not to require the use of
  `the DEP process`_.

* "Major Change" means any change to Django's codebase of scope
  significant enough to require the use of `the DEP process`_.

The following terms are used in this document to refer to types of
releases of Django:

* "Major Release Series" means the x.0 through x.2 releases of Django,
  for a given x. For example, Django 3.0, 3.1, and 3.2 collectively
  form a Major Release Series.

* "Feature Release" means an x.y.0 release of Django, where x.0 began
  a major release series and y is either 0, 1, or 2. For example,
  Django 3.1.0 is a Feature Release.

* "Bugfix Release" means an x.y.z release of Django, where z is not 0.
  For example, Django 3.1.4 is a Bugfix Release, while Django 3.1.0
  is a Feature Release.

* "Security Release" means a Bugfix Release which included a fix for a
  security issue in Django being handled under `Django's security
  process <https://www.djangoproject.com/security/>`_.


Specification
=============

How Django is developed
-----------------------

Everyone is encouraged to open tickets, triage tickets and perform code
reviews.

Commits can only be merged in by the `Mergers Team`_. A Merger can merge
their own commits if it's been reviewed by another Merger, the
`Triage & Review Team`_ or `Security Team`_. Members of the
`Releasers Team`_ can also merge commits when they are related to
releases.

A Minor Change that fails to reach consensus can be escalated to the
Steering Council for a final decision to merge.


How Django's technical direction is determined
----------------------------------------------

Everyone is encouraged to propose and provide feedback on new features
for Django at any time on the `new-features GitHub repository`_.

For features which qualify as a Major Change, proposers may be asked to
use `the DEP process`_. Likewise, other changes, for example to processes,
that do not fit the new features description may be presented as DEPs

If discussion of a Minor Change has failed to produce consensus, a
member may ask the Steering Council to make a decision.

Rejected discussions and features are eligible to be revisited at the
Steering Council's discretion.


How Django is released
----------------------

Only members of the `Releasers Team`_ may perform a release.

Django follows the time-based release schedule, as outlined in `DEP 44`_.

The `Security Team`_ may request a Security Release of Django. This
should be performed at or as close as is practicable to the time of
release requested by the `Security Team`_.


Steering Council role
---------------------

The Steering Council provides oversight of Django's development and
release process, assists in setting the direction of feature
development and releases, selects Mergers and Releasers, and has a
tie-breaking vote when other decision-making processes fail.

The Steering Council consists of five members.

The powers of the Steering Council are:

* To make a binding decision regarding any question of a technical
  change to Django.

* To manage the Steering Council's membership via an election with the
  `DSF Board`_.

* To create/update `teams`_

Steering Council's goals
++++++++++++++++++++++++

The Council's goal is twofold - to safeguard big decisions that affect
Django projects at a fundamental level, and to help shepherd the
project's future direction.

While the Council should not define this direction entirely by itself,
it should be the catalyst within the community for doing so - as such,
it is expected for Council members to actively participate in engaging
with the community, canvassing for ideas about big new features or
directions to take the framework, and reporting back to the community
and the DSF Board on these ideas and if the Council believes they
should be followed.


Decision making process of the Steering Council
+++++++++++++++++++++++++++++++++++++++++++++++

When asked to make a technical decision, the Steering Council should
first discuss this amongst themselves. If there's agreement on a course
of action, a single member will respond on the `Django Forum`_, ticket, or
`new-features GitHub repository`_ on behalf of the Steering Council. It
may optionally include a dissenting opinion if someone wishes to include one.


Steering Council eligibility
++++++++++++++++++++++++++++

To be eligible to be on the steering council, a person must do the following:

* Be a DSF Individual member.

* Shared any of their corporate affiliations.

* Have three or more Steering Council Qualities.

* Not be a members of the `DSF Board`_.

Steering Council Qualities
**************************

Below are several traits a Django contributor may possess that are beneficial
when on the Steering Council. An individual is unlikely to possess all of
them, but qualified candidates should have more than one. Each trait is
followed up by a set of possible indicators that could be evidence of this
trait. The lists of indicators are not complete, if you feel you possess that
trait with an indicator that's not listed, that is sufficient.

* `Community facilitator`_

* `Creator mentality`_

* `Dedication to the community`_

* `Forward thinking`_

* `Stewardship`_

* `Django usage expertise`_

* `Django education expertise`_

* `Django maintenance expertise`_

Community facilitator
*********************

We want people who are willing to facilitate communication and guide the
community. They should understand the challenges of volunteerism and support
people to be most effective. The Steering Council needs to help align the
community, and be an occasional, yet still reliable nudge to advance community
efforts.

Indicators:

* Led or shepherded one or several DEPs

* Led a working group or team, conference, organization

Creator mentality
*****************

We want people who are self-driven, willing to find problems and push
solutions forward. The Steering Council needs to take consistent, incremental
steps forward to implement its long-term strategies.

Indicators:

* Participated with one or several DEPs

* Participated in a related working group or team, conference, organization

* Maintained well-used Python/Django package

Dedication to the community
***************************

We want people who are invested in the community to lead it. This can be a
professional interest in seeing Django succeed or desire to repay the
community. The Steering Council needs to be trusted to act in the best
interest for the community.

Indicators:

* Multi-year Django user

* Multi-year Django community contributor

Forward thinking
****************

We want people who have a vision for Django that extends years into the
future. The Steering Council needs to plan and execute on long-term
strategies for Django.

Indicators:

* Participated with one or several DEPs

* Participated in a related working group or team, conference, organization

* Created content or participated in discussions on the topic

Stewardship
***********

We want people who understand Django's value of robustness and consistency.
The Steering Council needs to make decisions that keep Django reliable and
trusted.

Indicators:

* Participated with one or several DEPs

* Participated in a related working group or team, conference, organization

* Created content or participated in discussions on the topic

Django usage expertise
**********************

We want people who know how Django is used to build real-world applications.
The Steering Council needs to understand the needs of web applications and
experience with actual usage allows that.

Indicators:

* Experience building and maintaining production Django apps over years

* Has a network of people who maintain and build Django applications

Django education expertise
**************************

We want people who consider Django from a developer experience and education
point of view. The Steering Council needs to consider what it's like to learn
Django and how to be more effective with it.

Indicators:

* Content creator about Django

* Has contributed to Django documentation and/or support content

Django maintenance expertise
****************************

We want people who have a strong understanding of Django from the framework's
perspective. The Steering Council needs to be able to weigh technical
decisions appropriately and familiarity with the code supports that.

Indicators:

* Familiar with several areas of the Django codebase

* Has helped maintain Django or another well-used project for years


Steering Council elections
++++++++++++++++++++++++++

Whenever an election of the Steering Council is triggered, the
following limits are put in place until the election process is
complete:

* Any appointments to the roles of Merger and/or Releaser, other than
  of `Django Fellows`_, are temporary, and will require confirmation
  by the newly elected Steering Council.


Steering Council election triggers
**********************************

Elections of the Steering Council are triggered by any of the
following events:

* The final Feature Release of a Major Release Series of Django if
  no election of the Steering Council has yet occurred during that
  Major Release Series.

* The resignation or another event that leaves Steering Council with
  fewer than three elected members. This is to prevent the majority
  of the Steering Council consisting of appointed members appointments
  rather than elected members.

* The Steering Council votes to hold an election.

Steering Council voting eligibility
***********************************

All `DSF Individual members`_ are eligible to vote in elections
of the Steering Council.

Steering Council election process
*********************************

The DSF Board shall manage the election process. They can delegate
aspects of the process as needed.

The process of electing a Steering Council is as follows:

1. When an election is triggered, the Steering Council will notify the
   DSF Board, in writing, of the triggering of the
   election, and the condition which triggered it. The DSF Board
   then will post to the `Django Forum`_ and other appropriate
   venues to announce the election and its timeline.

2. As soon as the election is announced, the DSF Board shall begin a
   period of candidate registration. Any qualified person may register
   as a candidate; the candidate registration form and roster of
   candidates will be maintained by the DSF Board, and candidates must
   provide evidence of their qualifications as part of registration.
   The DSF Board can challenge and reject the registration of
   candidates it believes do not meet the qualifications of members of
   the Steering Council, or who it believes are registering in bad
   faith.

3. Registration of candidates will close two weeks after it has
   opened. After registration of candidates closes, the DSF Board will
   publish the roster of candidates to the Django Forum and any other
   appropriate venues, and the election will begin. The DSF Board will
   provide a voting form accessible to registered voters.

4. The voting system is selected by the DSF Board. Voting will be by secret
   ballot. Each voter will be presented with a ballot containing the roster
   of candidates, and any relevant materials regarding the candidates, in a
   randomized order.

5. The election will conclude three weeks after it begins. The DSF Board will
   tally the votes and produce a summary. This summary will be ratified by a
   majority vote of the DSF Board, then posted by the DSF Board to the Django
   Forum and any other appropriate venues. The five candidates with the
   highest vote totals will immediately become the new Steering Council.

Removing a single Steering Council member
*****************************************

A member of the Steering Council can be removed in the following
ways:

* They become ineligible due to actions of the Code of Conduct
  committee of the DSF. If this occurs, the affected person
  immediately ceases to be a member of the Steering Council. If that
  person's ineligibility ends at a later date, they may become a
  candidate for the Steering Council again in an election occurring
  after that date.

* It is determined that they did not possess the qualifications of a
  member of the Steering Council. This determination must be made
  jointly by the other members of the Steering Council, and the DSF
  Board. A valid determination of ineligibility requires that all
  other members of the Steering Council vote to declare the affected
  person ineligible and that all members of the DSF Board who can
  vote on the issue (the affected person, if a DSF Board member, can
  not vote) vote "yes" on a motion that the person in question is
  ineligible.

* A member of the Steering Council resigns from the Steering Council
  by notifying the other members of the Steering Council of their
  intent to resign.

The Steering Council should try to fill a vacancy on the Steering
Council. This may involve the departing member if they are eligible
and willing. The process is as follows:

* Any member of the Steering Council, including an otherwise
  eligible but departing member, may nominate a candidate to fill a
  vacancy.

* The Steering Council will notify the DSF Board, in
  writing, of the nomination. The DSF Board will check the
  qualifications of the person nominated, and the DSF Board
  will notify the Steering Council of the result. If the DSF
  Board determines the nominated person is not qualified, the
  nomination must be discarded.

* A qualified nominee will fill the vacancy if the Steering Council
  votes to appoint the nominee. As an exception to the Steering
  Council voting process described above, this vote must be completed
  within one-week and it must be unanimous approval.

Removing the entire Steering Council
************************************

Any Django Software Foundation individual member may make a public
statement of no-confidence in the Steering Council by identifying a
material breach of their duties as defined in the technical governance.
Upon seconding by another individual member of the DSF the DSF Board
will evaluate the merits of the statement of no-confidence in their
next meeting.

If the statement is found to be accurate and correct the DSF Board shall
inform the Steering Council of the breach and provide 2 weeks to
rectify said breach. If the Steering Council fails to rectify the
breach in the time allotted, a new Steering Council election will be
triggered. Current members of the Steering Council may run in the new
election.

Steering Council reports
++++++++++++++++++++++++

The Steering Council should produce reports of its actions and the state
of Django. To facilitate the standing goal of transparency, as appropriate,
and at their discretion the Steering Council may publish additional posts to
help communicate progress.

* The Steering Council's meeting minutes can be found in the
  `steering-council GitHub repository`_.

* The `Django features roadmap`_ for can be found in the
  `new-features GitHub repository`_


Teams
---------------

The Steering Council and `DSF Board`_ delegate certain responsibilities
and powers to various teams. These teams can be created without
changes to the technical governance document.

To see the list of teams and the process of adding new
teams, please see the `django/dsf-working-groups GitHub repository`_.


Interaction of the Steering Council and the Security Team
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

The `Security Team`_ has the following powers:

* To request a Merger merge code to fix a security issue being
  handled under Django's security process.

* To request a Releaser issue a release of Django containing code to
  fix a security issue being handled under Django's security
  process.

In the event that the Steering Council feels the Security Team has
used the above powers inappropriately, the Steering Council may appeal
to the DSF Board to mediate the issue. Any member of the DSF Board who
is also a member of the Security Team will
abstain from participation in the DSF Board's decision-making in such
mediation. The decision of the DSF Board in the dispute will be
binding on both the Steering Council and the Security Team.


Interaction of the Steering Council and other teams
+++++++++++++++++++++++++++++++++++++++++++++++++++

The Steering Council may oversee or have a liaison on various teams
and working groups in the Django community. In all cases the following
interactions should occur:

* The Steering Council may make requests of those teams, and those
  teams should accommodate those requests when reasonable and
  practicable.

* Those teams may make requests of the Steering Council, and the
  Steering Council should accommodate those requests when reasonable
  and practicable, provided that accommodating the request falls
  within the powers of the Steering Council.

In the event of a dispute between the Steering Council and a team,
the DSF Board shall serve as mediator. Any member of the DSF Board who
is also a member of the affected team will
abstain from the DSF Board's decision-making in such mediation. The
decision of the DSF Board in the dispute will be binding on both the
Steering Council and the affected team.


Changing this governance process
--------------------------------

Changes to this governance process shall be treated initially as
Major Changes to Django, and as such shall require the use of the DEP
process as described in DEP 1, with modifications as described below.

1. To reach the "accepted" state, a DEP proposing changes to this
   governance process must receive an outcome of "Accept" in a vote
   of the Steering Council with a score of at least 4, rather than
   the usual 3.

2. Once such a DEP reaches "accepted" status, the Steering Council
   will direct one of its members to notify `DSF Board`_,
   in writing, of the existence of an accepted DEP for changing the
   governance process.

3. The `DSF Board`_ will hold a vote on a motion to adopt the proposed
   change. If the DSF Board rejects the motion, the governance process
   will not change, and the DSF Board will notify the
   Steering Council, in writing, of the DSF Board's objections to the
   proposal. The DEP then returns to draft status. The DEP may be
   revised and restart the DEP approval process.

4. If the DSF Board accepts the motion, the DSF Board and the
   Steering Council will then hold separate votes on the question of
   whether the proposed change is significant enough to require
   approval by the community at large. If both the DSF Board and the
   Steering Council determine that the proposal is not significant
   enough to require such approval, the proposal then will be adopted
   and the DEP will immediately begin implementation.

5. If the DSF Board and/or the Steering Council determine that the
   proposal is significant enough to require approval by the
   community at large, the DSF Board will immediately call a special
   election. The qualifications of voters for the special election
   will be the same as those for elections of the Steering Council,
   and all persons eligible to vote for the Steering Council will
   automatically be eligible to vote in the special election. One
   week after that registration period closes, the special election
   will begin. Voting will be by secret ballot. Each voter will be
   presented with a ballot containing a link to the DEP, and links to
   any associated materials, and the question: "Shall the change to
   Django's governance, indicated above, be adopted?" Voters may vote
   "Yes", "No", or "Abstain" on the question. The election will
   conclude one week after it begins. The DSF Board will tally the
   votes and produce a summary, including the total number of votes
   cast and the number of votes for each option. If at least a
   plurality of votes cast are for "Yes", the proposal then will be
   adopted and the DEP will immediately begin implementation. If
   "Yes" does not achieve at least a plurality of votes cast, the
   proposal then will not be adopted and the DEP will return to to
   draft status. The DEP may be revised and restart the DEP approval
   process.


Motivation
==========

This is a revisitation of Django's technical governance in which a
simplification and reduction was made to make it more approachable to
more people. The goals of these changes are the following:

* Make it easier to enact our governance.

* Make it easier for others to understand our governance.

* Make the governance more flexible, allowing more action with less
  procedure.

It achieves those goals with the following:

* Presenting a merged governance document avoiding overruling
  governance documents (DEP 10 & 12).

* Reducing the number of sections and topics.

* Including more headings.

* Outsourcing specific topics such as releases and teams to other
  resources.

* Removing the RFC 2119 language.

* Reducing the scope of eligible voters to reflect and take
  advantage of the broader DSF Individual Membership eligibility.

* Allowing approving DEPs during elections.

* Allowing governance changing DEPs during elections.

* Allowing the Steering Council to revisit rejected discussions at
  their discretion.

* Not allowing Board members to serve on the Steering Council.

* Removing the explicit voting from the decision making of the Steering
  Council.

* Using a collection of qualities Steering Council candidates rather than
  specific eligibility prerequisites.

* Allowing the DSF Board greater autonomy in running the Steering Council
  elections.


Rationale
=========

Similar to DEP 12, this is another iteration on our governance. While
this is a significant change in terms of content, the spirit and intent
of Django's technical governance remains the same. All governance
requires periodic cultivation, and this should be seen as one of those
instances.

Regarding specific changes:

* Presenting a merged governance document avoiding overruling
  governance documents (DEP 10 & 12).

  * A single document avoids having to read two documents to
    understand the governance.

* Reducing the number of sections and topics.

  * DEP 10 sought to provide information on how the new governance
    would operate. While helpful in that moment, it eventually
    became a burden when revisiting the document.

* Including more headings.

  * Makes the document more accessible and makes it easier to
    find specific information.

* Outsourcing specific topics such as releases and teams to other
  resources.

  * This document has a high resistance to change. By moving topics
    such as membership requirements for `teams`_ to their own
    charters allows those teams to be more flexible. It's possible
    this document will refer to others, similar to `DEP 44`_ and the
    `How Django is released`_ section.

* Removing the RFC 2119 language.

  * This language made the document difficult to read. Removing it
    should help others read the document more easily and engage with
    the content more.

* Reducing the scope of eligible voters to reflect and take
  advantage of the broader DSF Individual Membership eligibility.

  * This reduces the amount of rules in the document, makes it easier
    to read and allows effectively the same number of people to
    participate in Steering Council elections.

* Allowing approving DEPs during elections.

  * The community and `DSF Board`_ both have mechanisms to remove an unruly
    Steering Council. These limitations appear to have only limited
    productive functions of the Steering Council. Allowing approving
    DEPs during elections allows for the community to operate more
    freely. It's possible that a newly elected Steering Council will
    change decisions from the previous Steering Council. This is seen
    as the system working. If at any point, the trust in this system
    is abused, the community can rely on reporting members for
    violations of Django's Code of Conduct.

* Allowing governance changing DEPs during elections.

  * Governance changing DEPs require an approval from the DSF Board. This
    limitation appears to only limit productive functions of the
    Steering Council. If an outgoing Steering Council attempts to
    enact undesirable changes at the end of their term, the DSF Board
    exists as the check. This allows the Steering Council to make
    changes that are productive during this time. A common governance
    change has been to revisit voting requirements. This usually
    becomes relevant right when an election is starting.

* Allowing the Steering Council to revisit rejected discussions at
  their discretion.

  * This prevents one Steering Council from limiting the next
    Steering Council in an undesirable fashion. If a community
    member is asking for discussions to be revisited frequently, to
    the extent of being annoying, that would be a Django Code of
    Conduct Violation.

  * This language was changed from vetoed to rejected to better match
    the decision making process for the Steering Council.

* Not allowing Board members to serve on the Steering Council.

  * This simplifies some of the governance by reducing exception cases.
    Plus, these roles are meant to be time-intensive and it's unlikely
    for someone to do both well.

* Removing the explicit voting from the decision making of the Steering
  Council.

  * This accurately reflects the process the 6.X Steering Council has
    been using. Future Steering Councils may internally decide to use
    voting, however it is not a necessary process. The discussion and
    deliberation is a more accurate representation of how the Django
    community arrives at consensus.

* Using a collection of qualities Steering Council candidates rather than
  specific eligibility prerequisites.

  * The specific eligibility requirements seemed to cause candidates to self-
    select out. By listing the qualities and traits a Steering Council member
    may have, a prospective candidate may feel more qualified to run. It has
    been difficult to quantify what experience will make a good Steering
    Council member. By leaning into the qualitative aspects, this should help
    make it easier to nominate yourself for the Steering Council.

* Allowing the DSF Board greater autonomy in running the Steering Council
  elections.

  * By not including as many requirements of the voting mechanics, the Board
    can integrate lessons learned from the DSF Board elections for the
    Steering Council.

Backwards Compatibility
=======================

This document supersedes both DEP 10 and DEP 12.


Reference Implementation
========================

N/A


Copyright
=========

This document has been placed in the public domain per the Creative
Commons CC0 1.0 Universal license
(http://creativecommons.org/publicdomain/zero/1.0/deed).

(All DEPs must include this exact copyright statement.)

.. _DEP 44: https://github.com/django/deps/blob/main/accepted/0044-clarify-release-process.rst
.. _Mergers Team: https://github.com/django/dsf-working-groups/blob/main/active/mergers-team.md
.. _Releasers Team: https://github.com/django/dsf-working-groups/blob/main/active/releasers-team.md
.. _Security Team: https://github.com/django/dsf-working-groups/blob/main/active/security-team.md
.. _Triage & Review Team: https://github.com/django/dsf-working-groups/blob/main/active/triage-and-review-team.md
.. _django/dsf-working-groups GitHub repository: https://github.com/django/dsf-working-groups
.. _new-features GitHub repository: https://github.com/django/new-features
.. _the DEP process: https://github.com/django/deps/blob/main/final/0001-dep-process.rst
.. _DSF Individual Members: https://www.djangoproject.com/foundation/individual-members/
.. _DSF Board: https://www.djangoproject.com/foundation/#board
.. _Django Fellows: https://www.djangoproject.com/foundation/teams/#django-fellows-team
.. _teams: https://www.djangoproject.com/foundation/teams/
.. _Django Forum: https://forum.djangoproject.com/
.. _steering-council GitHub repository: https://github.com/django/steering-council
.. _Django features roadmap: https://github.com/orgs/django/projects/24
