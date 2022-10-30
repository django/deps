==============================
DEP 0012: The Steering Council
==============================

:DEP: 0012
:Author: Andrew Godwin
:Implementation Team: Andrew Godwin
:Shepherd: Carlton Gibson
:Status: Draft
:Type: Process
:Created: 2022-10-26
:Last-Modified: 2022-10-26

.. contents:: Table of Contents
   :depth: 3
   :local:


Abstract
========

The Technical Board, as defined in `DEP 10 <https://github.com/django/deps/blob/main/accepted/0010-new-governance.rst>`_, will be renamed to the Steering
Council, the eligibility requirements for becoming a candidate will be
revised, and a renewed focus will be placed on inviting feature changes.


Specification
=============

The Technical Board, as specified in DEP 10, will be renamed to the Steering
Council. All other aspects of DEP 10 will continue to apply unless noted below.

The existing requirements to be qualified for election to the Steering Council
will be replaced with requiring both of the following:

* A history of substantive contributions to Django or the Django
  ecosystem. This history must begin at least 18 months prior to the
  individual's candidacy for the Steering Council, and include substantive
  contributions in at least two of these bullet points:

  * Code contributions on Django projects or major third-party packages in
    the Django ecosystem

  * Reviewing pull requests and/or triaging Django project tickets

  * Documentation, tutorials or blog posts

  * Discussions about Django on the django-developers mailing list or the
    Django Forum

  * Running Django-related events or user groups

* A history of engagement with the direction and future of Django.
  This does not need to be recent, but candidates who have not engaged in the
  past three years must still demonstrate an understanding of Django's changes
  and direction within those three years.

Additionally, the following section is added to the definition of
the Steering Council to make its role clearer:

  The Council's goal is twofold - to safeguard big decisions that affect
  Django projects at a fundamental level, and to help shepherd the project's
  future direction.

  While the Council should not define this direction entirely by itself,
  it should be the catalyst within the community for doing so - as such, it is
  expected for Council members to actively participate in engaging with the
  community, canvassing for ideas about big new features or directions to take
  the framework, and reporting back to the community and the DSF Board on these
  ideas and if the Council believes they should be followed.


Motivation
==========

While the model outlined by DEP 10 is still valid, the last few Technical
Boards have not done the entire role in the way that was originally
envisioned - instead, mostly acting as a last-hurdle approval on DEPs and
appointments to other positions.

In recent elections we have also faced a lack of candidates, culminating in the
most recent one, where we had only five candidates for five positions. It is
not just Django specific - talking to friends who help with other Open Source
projects in a variety of languages, and indeed to non-profits at large, this
appears to be a wider trend.

In order to get closer to the initial intention, we want to make the Board more
active, but it is apparent that, to do this, we must staff it more sustainably.

As such, this DEP does two things:

* Makes the Board's role more clear by renaming it (Steering Council implies
  the job of "working out what features and direction to go" more than
  Technical Board does) and by specifically adding language highlighting the
  more active role expected of its members.

* Increases the number of people eligible for candidacy on the Council in
  order for us to sustainably staff it for the foreseeable future, while not
  making the rules so loose that it risks hostile takeovers.

It refrains from making any further changes under the belief that good progress
is incremental - take a model, refine it slightly, and then if we continue to
see problems, we should react to those. If the path suggested by this DEP does
not improve matters by the end of the 5.x release series, it is the author's
belief that further changes may be necessary.


Rationale
=========

While we could try and redo our governance process far more drastically, the
author believes that the model outlined in DEP 10 is fundamentally sound and merely
needs a few tweaks as the demographics of who is willing to step up and help
steer Django has changed over the years.

We also could do nothing, but the author thinks that would be foolish in the face of the
current approach (which is not what was outlined in DEP 10 anyway) not working.
Change is needed, and the author believes this is the right line between iterative
changes and overhaul.


Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).

(All DEPs must include this exact copyright statement.)
