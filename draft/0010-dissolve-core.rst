================================
DEP 0010: Dissolving Django Core
================================

:DEP: 0010
:Author: James Bennett
:Implementation Team: James Bennett, others to be determined
:Shepherd: Aymeric Augustin
:Status: Draft
:Type: Process
:Created: 2018-09-22
:Last-Modified: 2019-06-10

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

* "Django core": the set of people who have or have had permission to
  push to <https://github.com/django/django/> or the previous
  Subversion repository, or who have been members of the django-core
  mailing list, the #django-core IRC channel, or identified as members
  of "Django core" on the djangoproject.com website.

* "DSF Board": the Board of Directors of the Django Software
  Foundation.

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

1. Removing push access to <https://github.com/django/django/> from
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
as three specialized roles.

The full details follow below, but a short description is:

* Membership in the Framework team is generally open to the public
  (with the primary exception of individuals ineligible due to actions
  of the Code of Conduct committee of the Django Software Foundation,
  or removal by the Technical Board), and members can take part in
  discussion and decision-making, and vote in elections of the
  Framework team.

* A new role, Merger, will consist of being responsible for
  merging pull requests.

* A second new role, Releaser, will consist of being responsible for
  issuing new packaged releases of Django.

* Technical decision-making will occur on the django-developers
  mailing list, with participation open to any member of the Framework
  team. Decisions will be made by voting, with Mergers keeping track
  of votes to determine if a consensus exists toward a particular
  decision.

* A Technical Board, elected by the Framework team, will exist as a
  tie-breaker and to provide oversight of the Mergers.


New role: Merger
----------------

In place of the committer, Django will formalize and expand the *de
facto* process already in place: the role of the Merger. A Merger is a
person who merges pull requests to https://github.com/django/django/.

The set of Mergers should be small; the ideal would be between three
and five people, in order to spread the workload and avoid
over-burdening or burning out any individual Merger. In light of that,
the current Django Fellows will become the first set of
Mergers. Thereafter, the Technical Board will select Mergers as
necessary to maintain their number at a minimum of three.

It shall not be a requirement that a Merger also be a Django Fellow,
but the Django Software Foundation shall have the power to use funding
of Fellow positions as a way to make the role of Merger sustainable.


New role: Releaser
------------------

Over its history, the Django project has granted various people
permission to issue packaged releases of Django. At present five
people have permission to upload releases to the Python Package Index.

The role of Releaser will formalize this permission: a Releaser is a
person who has the authority (and will be granted the necessary
permissions) to upload packaged releases of Django to the Python
Package Index, and to djangoproject.com.

A person may serve in the roles of Releaser and Merger simultaneously.

The initial set of Releasers will consist of the Django
Fellows. Thereafter, the Technical Board will select Releasers as
necessary to maintain their number at a minimum of three.

It shall not be a requirement that a Releaser also be a Django Fellow,
but the Django Software Foundation shall have the power to use funding
of Fellow positions as a way to make the role of Releaser sustainable.

Releasers will issue new releases of Django under the following
circumstances, using the terminology for releases outlined at
<https://docs.djangoproject.com/en/dev/internals/release-process/>:

* Scheduled patch releases of supported versions of Django, on or
  about the first day of each calendar month, unless directed to wait
  by the Technical Board.

* Security releases, at the request of the Django security team.

* Feature releases, when the Technical Board agrees that the feature
  release is ready.

* Alpha and beta releases at scheduled times to be determined by the
  Framework team.

* Release candidate releases at scheduled times to be determined by
  the Framework team.


Repurposed role: Technical Board
--------------------------------

The Framework team shall elect a Technical Board. The mechanics and
timing of elections are discussed further below.

The Technical Board will provide oversight of the development and
release process, take part in filling certain roles, and have a
tie-breaking vote when normal decision-making processes fail.

The Technical Board will consist of five members, elected from among
the membership of the Framework team. To be qualified for election to
the Technical Board, a member of the Framework team must demonstrate:

* A history of technical contributions to Django or the Django
  ecosystem. This history should begin at least 18 months prior to the
  individual's candidacy for the Technical Board.

* A history of participation in Django's development outside of
  contributions merged to the <https://github.com/django/django/>
  repository. This may include, but is not restricted to:
  participation in discussions on the django-developers mailing list;
  reviewing and offering feedback on pull requests in the Django
  source repository; and assisting in triage and management of the
  Django bug tracker.


How code is added to Django
---------------------------

Any Merger may, on their own initiative, merge any pull request other
than one authored by that Merger. Mergers will be trusted to use their
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

* When a release of Django is ready, Mergers and Releasers may also
  make such commits as are necessary to carry out the mechanics of
  releasing Django (such as changing version numbers in configuration
  files, creating or updating release branches and tags, and so on).


The Framework team
------------------

The process of adding code to Django will be governed by a Framework
team. Membership in this team is open to anyone who wants it, and the
business of the Framework team will be carried out in public on the
django-developers mailing list. Membership in the Framework team shall
be conferred automatically upon joining that mailing list, and
includes the right to vote in technical decisions. Voting privileges
for elections of the Technical Board will be conferred as explained
below, in the section regarding elections of the Technical Board.

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

A member of the Framework team can be removed in either of two ways:

* By becoming ineligible due to action of the Code of Conduct
  committee of the Django Software Foundation, or

* By unanimous vote of the Technical Board.

A person removed from the Framework team may be removed from the
django-developers mailing list, and have their permissions to interact
in other technical spaces (such as the bug tracker, or GitHub)
revoked.

No vote of the Technical Board shall be required to remove a person
from the django-developers mailing list, or revoke their access to
other technical spaces, in the event that the designated
administrators of those spaces feel a person has engaged in spamming
behavior.


Role of the Technical Board in decision-making
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Technical Board will provide oversight of the release
process. While some releases (monthly patch releases, and alpha/beta
versions of feature releases) will occur on pre-determined schedules,
feature releaes of Django will occur once the Technical Board has
approved, by public vote, the state of the codebae for the proposed
release.

The Technical Board shall have the prerogative to set the dates of its
own elections, or to fill vacancies in the Technical Board, using the
voting process outlined below, but subject to the constraints
specified elsewhere in this document on eligibility, the selection
process, and the frequency of elections.

The Technical Board shall also appoint Releasers and Mergers as needed
to fill vacancies in that role, using the voting process outlined
below. Nominations to fill these roles can be suggested by any member
of the Framework team, but only formally put to the Technical Board by
a member of the Technical Board.

If the Technical Board feels that a member of the Framework team has
acted in bad faith incompatible with continued membership, or in a
manner otherwise disruptive to the development of Django, any member
of the Technical Board may nominate that person for removal from the
Framework team. The Technical Board shall then vote on the matter, and
a unanimous vote in favor of removal will result in that person's
removal, either for a set time or permanently.

The Technical Board shall also act as a tie-breaker in the event that
a discussion of the Framework team fails to achieve consensus. If any
member of the Framework team feels productive discussion of a topic
has been exhausted without achieving consensus, they may request a
decision of the Technical Board. The Technical Board may, at its
discretion, decline and encourage further discussion, or may accept
the issue and make a decision using the voting process outlined below.


Voting process of the Technical Board
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a vote of the Technical Board is required, they shall use the
following process:

1. Each member of the Technical Board shall have, from the time a
   question is put to them, one week to review the question and vote.

2. Votes shall be made in public, on the django-developers mailing
   list.

3. Each vote shall be of the form "+1" (in favor) or "-1" (not in
   favor). Each member should also provide, along with their vote,
   their rationale for voting as they did.

4. Once sufficient votes in either direction have been cast to form a
   majority of the Technical Board, a call will be made for the
   remaining memebers to cast their votes. They shall have until the
   normal close of voting (one week from the question being put to the
   Technical Board) in which to do so.

5. If the voting period closes without all members of the Technical
   Board having voted, but with a majority of the members voting for
   one of the options, that shall be the result of the vote.

6. If the voting period closes without all members of the Technical
   Board having voted, and no option won a majority of the votes cast,
   the voting period shall be extended one week. This process shall
   repeat until one of the options receives the endorsement of a
   majority of members of the Technical Board.

Votes of the Technical Board are binding. All members of the Framework
team, including all Mergers and Releasers, are expected to abide by
these decisions.

Members of the Framework team may request that the Technical Board
revisit or reconsider a prior question, but not until at least six
months have elapsed since the time of the Technical Board's most
recent vote on that question.

Members of the Technical Board may request that the Technical Board
revisit a prior question at any time, but the Technical Board may
refuse the request.


Process of selecting Mergers and Releasers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As noted above, the initial set of Mergers and Releasers will be the
current Django Fellows. The Framework team shall then work to select
at least one additional Merger, and shall at all times attempt to
maintain a roster of at least three Mergers, and as many Releasers as
are deemed necessary to meet needs.

The selection process for either role shall occur as follows:

* Any member of the Framework team may suggest a person for
  consideration.

* The Technical Board shall consider the suggestions put forth, and
  then any member of the Technical Board may formally nominate a
  person for the role to be filled.

* The Technical Board will then vote on the nomination, and the result
  of that vote shall either grant the role to the person nominated (if
  a majority are in favor), or not (if a majority are against).

The following restrictions will apply to nominations:

* No person shall simultaneously serve as a Merger and as a member of
  the Technical Board.

* No person who is ineligible to participate in public Django spaces
  due to action of the Code of Conduct committee of the Django
  Software Foundation may serve in the role of Releaser or the role of
  Merger.

Mergers may resign their role at any time, but are encouraged to
provide some advance notice in order to allow the selection of a
replacement. Termination of the contract of a Django Fellow by the
Django Software Foundation will temporarily suspend a Merger's role
until such time as the Technical Board can convene to determine a
course of action; they may, by majority vote, choose to retain the
Merger in that role, or to remove the Merger.

Otherwise, a Merger may only be removed by:

* Becoming disqualified due to election to the Technical Board, or

* Becoming disqualified due to actions taken by the Code of Conduct
  committee of the Django Software Foundation, or

* A unanimous vote of the Technical Board.

A simple majority vote of the Technical Board may, at the request of a
member of the Technical Board, temporarily suspend a person from the
role of Releaser or Merger until such time as discussion and voting
can take place regarding permanent removal.


Process of selecting the Technical Board
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The initial Technical Board shall be made up of the final technical
board elected by the dissolved Django core. They shall consult with
the Framework team membership, and then decide whether to call an
election immediately, or wait until the next scheduled election (see
below for how often Technical Board elections shall occur).

Members of the Framework team are not required to vote in elections
for the Technical Board, but any registered voting member of the
Framework team may vote in any election. Although the Technical Board
is subject to certain qualifications, no history of technical
contributions to Django shall be required of voters.

The DSF Board will act as a neutral arbiter and judge of technical
board elections. Members of the DSF Board can stand for election to
the Technical Board if qualified, but any DSF Board member who is a
current member of the Technical Board or a candidate in an upcoming
election shall be required to abstain from taking part in the DSF
Board's oversight of that Technical Board election. The DSF Board
shall have the authority to delegate aspects of its oversight
responsibilities (such as the technical details of constructing
registration and voting forms) if it chooses to do so, but only the
DSF Board may ratify the results of a Technical Board election.

The process of electing a Technical Board shall be as follows:

1. The existing Technical Board will post to the django-developers
   mailing list to announce an election.

2. As soon as the election is announced, registration of voters will
   open. Any member of the Framework team who has not previously
   registered to vote may do so. The registration form and roll of
   voters will be overseen by the DSF Board. The DSF Board may
   challenge and reject the registration of voters it believes are
   registering in bad faith.

3. Registration of voters will close two weeks after the announcement
   of the election. At that point, registration of candidates will
   begin. Any qualified member of the Framework team may register as a
   candidate; the candidate registration form and roster of candidates
   will be overseen by the DSF Board, and candidates will be required
   to provide evidence of their qualifications as part of
   registration. The DSF Board may challenge and reject the
   registration of candidates it believes do not meet the
   qualifications of members of the Technical Board.

4. Registration of candidates will close two weeks after it has
   opened. One week after registration of candidates closes, the
   roster of candidates will be posted to the django-developers
   mailing list, and the election will begin. The DSF Board will
   provide a voting form accessible to registered voters, and shall be
   the custodian of the votes.

5. Voting shall be by secret ballot. Each voter will be presented with
   a ballot containing the roster of candidates, and any relevant
   materials regarding the candidates, in a randomized order. Each
   voter may vote for up to five candidates on the ballot.

6. The election will end one week after it begins. The DSF Board shall
   tally the votes and produce a summary, including the total number
   of votes cast and the number received by each candidate. This
   summary shall be ratified by a majority vote of the DSF Board, then
   posted to the django-developers mailing list. The five candidates
   with the highest vote totals will then become the new Framework
   team Technical Board.

Django's release cycle currently consists of a major series with three
minor releases. For example, the 2.x major series will include the
minor releases 2.0, 2.1 and 2.2, after which the 3.x major series will
begin.

At least one election of the Technical Board must occur for each major
series. If the final minor release of a major series is issued, and no
election has yet taken place, an election shall automatically be
triggered. The Technical Board may, at its discretion, choose to run
elections more often, but not more often than once per minor release.

In the event a member of the Technical Board is temporarily unable to
serve, the Technical Board will continue to carry out its duties
unless it would be reduced to fewer than three active members; in that
case, the Technical Board may, by majority vote, appoint a person (who
is otherwise qualified for the Technical Board) to serve until such
time as at least three elected members are able to serve again, or the
next election is held.

Members of the Technical Board cannot be removed from the Technical
Board once elected, unless it is determined by a unanimous vote of the
other Technical Board members and the DSF Board that they did not
possess the appropriate qualifications for the Technical Board, or
they become disqualified due to actions taken by the Code of Conduct
committee of the Django Software Foundation. In the event that a vote
is held to determine whether a person did not possess the relevant
qualifications, that person shall be barred from taking pert in the
vote in both the Technical Board and, if that person is also a member
of the DSF Board, the Technical Board shall not consider that person's
vote in the DSF Board for purposes of determining unanimity.


Motivation
==========

Django has been a very successful open-source project, but faces
certain threats to its long-term viability. Among those is the small
size (relative to the number of users of Django, and even to the
number of people who participate in the development of Django, either
on the django-developers mailing list or in the GitHub repository) and
stagnant nature of Django core. New members are added at a very low
rate, and most people who have been members now rarely, if ever, make
use of their ability to push code to Django.

Furthermore, the current state of Django's codebase seems not to be
amenable to ongoing recruitment of new members to Django core; several
people have expressed the opinion (or variations on it) that most of
the types of issues traditionally used as an entry route to core are
now resolved, and it's unclear what the path to core membership would
look like without such issues as a route to familiarity with
contributing to Django.

Finally, the existence of Django core is itself a barrier to
involvement; it has repeatedly been reported that potential
contributors are discouraged by the feeling that they are not "good
enough" to compare to the existing memebrs of Django core, and thus
could not make worthy contributions. This appears to be most acute
with recruitment of more diverse contributors to Django; the
demonstrated reach of the Django project, especially due to numerous
workshops and tutorials run around the world, does not match the
observed demographics of actual contributors of any type, let alone
members of Django core.

The primary goal of this proposal is to remove the perceived status
associated with permission to push code to the primary Django
source-code repository, and to re-frame the ability to push code to
that repository as more of a bureaucratic role which carries with it
no special privileges or status of any sort. Recognition of
contributions to Django or the Django ecosystem should be handled by
some type of status or award to be made by the Django Software
Foundation, rather than by push permission to a repository.

It is accepted that this is only the *first* step in a process of
encouraging and growing the number and diversity of contributors to
Django, and that further steps will need to be taken. But although it
is not *sufficient* to solve all of the above problems, this proposal,
or something similar to it, is *necessary* to begin the process of
solving these problems.


Rationale
=========

Dissolving or reorganizing Django core is a recurring issue within
Django core, the broader community of Django developers, and the
DSF. In particular, there seems to be a consensus to remove the
perceived bump in status asociated with membership in Django core,
especially as many people who could claim this membership are no
longer active in contributing to or shepherding the development of
Django. This DEP attempts to act on that consensus by providing a
concrete proposal.


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