======================
DEP XXXX: DEP template
======================

:DEP: XXXX
:Author: James Bennett
:Implementation Team: James Bennett, others to be determined
:Shepherd: TBD
:Status: Draft
:Type: Process
:Created: 2018-09-22
:Last-Modified: 2018-09-22

.. contents:: Table of Contents
   :depth: 3
   :local:


Abstract
========

This is a proposal to reform the organization of the Django
open-source project, by dissolving the current team of committers and
replacing it with a new governance model.

For clarity, this DEP uses the following terms to refer to existing
groups:

* "Django core": the set of people who have or had had permission to
  push to <https://github.com/django/django/>, or who have been
  members of the django-core mailing list, the #django-core IRC
  channel, or identified as members of "Django core" on the
  djangoproject.com website.

* "DSF Board": the Board of Directors of the Django Software
  Foundation

* "Django Fellows": a list of multiple people who have been, and in
  two cases still are, paid by the Django Software Foundation to
  perform various tasks, including triaging issues, reviewing and
  merging pull requests, and managing Django's releases.

This proposal deals only with replacing "Django core" as defined
above. No other team or group within the Django community is
considered here, nor will any other team or group be considered; the
scope of this proposal is solely "Django core".

Specification
=============

Django core will be dissolved. This would involve:

1. Removing push access to https://github.com/django/django/ from
   nearly all people who currently have it.

2. Closing the django-core mailing list and the #django-core IRC
   channel.

3. Ceasing to recognize any special status within the Django
   open-source project for people who formerly had push access or were
   members of the django-core mailing list or #django-core IRC
   channel.

In its place, the following model will be adopted for management of
Django's code:

The Django framework's codebase shall be governed by a new Framework
team. The Framework team will be made up of general members, as well
as two specialized roles.

The full details follow below, but a short description is:

* Anyone who joins the django-developers mailing list is a member of
  the Framework team, and can take part in discussion, decision-making
  and elections.

* A new role, Merger, exists and will consist of being responsible for
  merging pull requests.

* Decision-making will occur on the django-developers mailing list,
  with participation open to anyone. Decisions will be made by voting,
  with Mergers keeping track of votes to determine if a consensus
  exists toward a particular decision.

* A technical board, elected by the Framework team, will exist as a
  tie-breaker and to provide oversight of the Mergers.

New role: Merger
----------------

In place of the committer, Django will formalize and expand the *de
facto* process already in place: the role of the Merger. A Merger is a
person who merges pull requests to https://github.com/django/django/.

The set of Mergers should be small; the ideal would be between three
and five people, in order to spread the workload and avoid
over-burdening or burning out any individual Merger. in light of that,
the current Django Fellows will become the first set of Mergers, and
recruitment should begin imediately thereafter to bring the number of
Mergers up to at least three. It shall not be a requirement that a
Merger also be a Django Fellow, but the Django Software Foundation
shall have the power to use funding of Fellow positions as a way to
make the role of Merger sustainable.

Mergers shall also have the authority to make releases of Django,
including uploading packages to the Python Package Index and to the
djangoproject.com servers, according to release schedules determined
by the consensus of the Framework team.


Repurposed role: Technical board
--------------------------------

The Framework team shall elect a technical board. The mechanics and
timing of elections are discussed further below.

The technical board will provide oversight and a tie-breaking vote
when normal decision-making processes fail.

The technical board will consist of five members, elected from among
the membership of the Framework team. To be qualified for election to
the technical board, a member of the Framework team must demonstrate:

* A history of technical contributions to Django. This should involve
  some minimum number of merged contributions; at least five, and
  probably ten, with the first merged contribution occurring at least
  18 months prior to election to the technical board.

* A history of participation in Django's development outside of
  contributions merged to the https://github.com/django/django/
  repository. This may include, but is not restricted to:
  participation in discussions on the django-developers mailing list;
  reviewing and offering feedback on pull requests in the Django
  source repository; and assisting in triage and management of the
  Django bug tracker.


How code is added to Django
---------------------------

Any Merger may, on their own initiative, merge any pull request other
than one authored by that Marger. Mergers will be trusted to use their
judgment in deciding whether to merge any given pull request.

Mergers should, however, wait to merge any pull request which adds a
significant new feature or API, or makes significant changes to an
existing feature or API, until discussion has occurred on the
django-developers mailing list. Any Merger may ask that the author of
a pull request begin such a discussion, or a Merger may make the
initial post to django-developers, and from that point the pull
request shall not be merged until at least one week has elapsed, from
the date of the first post in the django-developers thread, for
discussion of it.

The only other methods for adding code to Django are:

* Patches generated by the Django security team for the purpose of
  resolving security issues in Django. Once such a patch is signed off
  by the security team, it can and shall be merged by a Merger on the
  designated disclosure date.

* When a release of Django is ready, Mergers may also make such
  commits as are necessary to carry out the mechanics of releasing
  Django (such as changing version numbers in configuration files,
  creating or updating release branches, and so on).


The Framework team
------------------

The process of adding code to Django will be governed by a Framework
team. Membership in this team is open to anyone who wants it, and the
business of the Framework team will be carried out in public on the
django-developers mailing list. Membership in the Framework team shall
be conferred automatically upon joining that mailing list.

The Framework team shall operate on a consensus model. Whenever any
member of the Framework team wishes to get feedback on code, design
decisions or other technical proposals, they will post a summary to
the django-developers list for discussion. Any member of the Framework
team may respond and state their opinions or arguments for or against
the proposal, and their vote if they wish to make one. Votes shall be
of the form "+1" (in favor) or "-1" (not in favor). There shall be no
explicit "abstain", "0", "+0" or "-0" votes. Any member wishing to
participate in a discussion without casting a vote may simply do so,
with no need to announce an abstention.

Mergers may request that a discussion close and any interested members
cast their votes; after making such a request, Mergers should wait at
least one week before treating the discussion and voting as closed.

Mergers shall use the results of votes cast in the discussion as a
guide to their actions; their judgment will be trusted in determining
whether a consensus has formed for or against.


Role of the technical board in decision-making
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If any member, including a Merger, feels productive discussion of a
topic has been exhausted without achieving consensus, they may request
a decision of the technical board. The technical board shall then
review the discussion up to that point, and each technical board
member shall cast a vote of either "+1" (in favor) or "-1" (not in
favor). Members of the technical board will cast their votes publicly
on the django-developers mailing list, and should provide explanations
of their votes when doing so. Members of the technical board should
cast their votes within one week of the request for a decision.

Once sufficient votes on either side have been cast to form a majority
of the technical board, a call will be made for the remaining members
to cast their votes. They shall have one week from that point to cast
their votes, or the discussion and vote will close automatically, with
the decision made in favor of the side carrying the majority of the
technical board's votes.


Process of selecting Mergers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As noted above, the initial set of Mergers will be the current Django
Fellows. The Framework team shall then work to select at least one
additional Merger, and shall at all times attempt to maintain a roster
of at least three Mergers. The Framework team shall keep in mind the
need for sufficient time-zone coverage to ensure availability of at
least one Merger during sprints at major events such as
DjangoCons. Mergers are not required to attend DjangoCons, but are
encouraged to do so and to be present for development sprints; the
Django Software Foundation shall have the power to grant funding for
the purpose of making Mergers' attendance at DjangoCons easier.

Upon adoption of this proposal, the initial set of Mergers, and the
technical board, shall work together to design a process for selecting
future Mergers, and prior to adoption of that process, shall post it
to the django-developers mailing list for feedback and voting. The
consensus model described above will be used to determine whether to
adopt the process, but in the event of no clear consensus the result
shall be that the process is not adopted, and a new process shall be
drafted taking into account the feedback obtained from discussion.

Whatever process is adopted, no person shall simultaneously serve as a
Merger and as a member of the technical board.

Mergers may resign their role at any time, but are encouraged to
provide some advance notice in order to allow the selection of a
replacement. Termination of the contract of a Django Fellow by the
Django Software Foundation will temporarily suspend a Merger's role
until such time as the technical board can convene to determine a
course of action; they may, by majority vote, choose to retain the
Merger in that role, or to remove the Merger.

Otherwise, a Merger may only be removed by:

* Becoming disqualified due to election to the technical board, or

* Becoming disqualified due to actions taken by the Code of Conduct
  committee of the Django Software Foundation, or

* By a unanimous vote of the technical board and all other current
  Mergers.


Process of selecting the technical board
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The initial technical board shall be made up of the final technical
board elected by the dissolved Django core. They shall consult with
the Framework team membership, and then decide whether to call an
election immediately, or wait until the next scheduled election (see
below for how often technical board elections shall occur).

Members of the Framework team are not required to vote in elections
for the technical board, but any member of the Framework team may vote
in any election. Although the technical board is subject to certain
qualifications, no history of technical contributions to Django shall
be required of voters.

The DSF Board will act as a neutral arbiter and judge of technical
board elections. Members of the DSF Board can stand for election to
the technical board if qualified, but any DSF Board member who is a
current member of the technical board or a candidate in an upcoming
election shall be required to abstain from taking part in the DSF
Board's oversight of the technical board election. The DSF Board shall
have the authority to delegate aspects of its oversight
responsibilities (such as the technical details of constructing
registration and voting forms) if it chooses to do so, but only the
DSF Board may ratify the results of a technical board election.

The process of electing a technical board shall be as follows:

1. The existing technical board will post to the django-developers
   mailing list to announce an election.

2. As soon as the election is announced, registration of voters will
   open. Any member of the Framework team may register to vote in the
   election; members must register for each election in which they
   wish to participate. The registration form and roll of voters will
   be overseen by the DSF Board. The DSF Board may challenge and
   reject the registration of voters it believes are registering in
   bad faith.

3. Registration of voters will close two weeks after the announcement
   of the election. At that point, registration of candidates will
   begin. Any qualified member of the Framework team may register as a
   candidate; the candidate registration form and roster of candidates
   will be overseen by the DSF Board, and candidates will be required
   to provide evidence of their qualifications as part of
   registration. The DSF Board may challenge and reject the
   registration of candidates it believes do not meet the
   qualifications of members of the technical board.

4. Registration of candidates will close two weeks after it has
   opened. One week after registration of candidates closes, the
   roster of candidates will be posted to the django-developers
   mailing list, and the election will begin. The DSF Board will
   provide a voting form accessible to registered voters, and shall be
   the custodian of the votes.

5. The election will end one week after it begins. The DSF Board shall
   tally the votes and produce a summary, including the total number
   of votes cast and the number received by each candidate. This
   summary shall be ratified by a majority vote of the DSF Board, then
   posted to the django-developers mailing list. The five candidates
   with the highest vote totals will then become the new Framework
   team technical board.

Django's release cycle currently consists of a major series with three
minor releases. For example, the 2.x major series will include the
minor releases 2.0, 2.1 and 2.2, after which the 3.x major series will
begin.

At least one election of the technical board must occur for each major
series. If the third minor release of a major series is issued, and no
election has yet taken place, an election shall automatically be
triggered. The technical board may, at its discretion, choose to run
elections more often, but not more often than once per minor release.

In the event a member of the technical board is temporarily unable to
serve, the technical board will continue to carry out its duties
unless it would be reduced to fewer than three active members; in that
case, the technical board may, by majority vote, appoint a person (who
is otherwise qualified for the technical board) to serve until such
time as at least three elected members are able to serve again.

In the event a member of the technical board becomes unable to serve
for a period of time lasting until at least the next scheduled
election, the technical board will continue to carry out its duties
unless it would be reduced to fewer than three active members; in that
case, the technical board may, by majority vote, appoint a person (who
is otherwise qualified for the technical board) to serve until the
next election.

Members of the technical board cannot be removed from the technical
board once elected, unless it is determined by a unanimous vote of the
other technical board members and the DSF Board that they did not
possess the appropriate qualifications for the technical board, or
they become disqualified due to actions taken by the Code of Conduct
committee of the Django Software Foundation.


Motivation
==========

The state of Django core is, at best, stagnant. New members are added
at a very slow rate, and most existing members rarely if ever make use
of their ability to push code to Django. Furthermore, the current
state of Django's codebase seems not to be amenable to ongoing
recruitment of new members to Django core; several people have
expressed the opinion (or variations on it) that most of the types of
issues traditionally used as an entry route to core are now resolved,
and it's unclear what the path to core membership would look like
without such issues as a route to familiarity with contributing to
Django.

There is also a serious, ongoing lack of diversity in Django core, and
no clear path to addressing it. The changes proposed here are not
sufficient to resolve this, but some type of change along these lines
is likely a necessary step toward other initiatives which could
resolve it.

The primary goal of this proposal is to remove the perceived status
associated with being able to push code to the primary Django
source-code repository, and to re-frame the ability to push code to
that repository as more of a bureaucratic role which carries with it
no special privileges or status of any sort.

Rationale
=========

Dissolving or reorganizing Django core is a recurring issue within
core, the broader community of Django developers, and the DSF. In
particular, there seems to be a consensus to remove the perceived bump
in status asociated with membership in Django core. This DEP attempts
to act on that consensus by providing a concrete proposal.

Backwards Compatibility
=======================

N/A

Reference Implementation
========================

N/A

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).

(All DEPs must include this exact copyright statement.)