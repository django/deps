=================================
DEP 1: DEP Purpose and Guidelines
=================================

:DEP: 1
:Author: Adrian Holovaty, Jacob Kaplan-Moss
:Status: Final
:Type: Process
:Created: 2014-04-14
:Last-Modified: 2023-10-21 

.. contents:: Table of Contents
   :depth: 3
   :local:

What is a DEP?
==============

DEP stands for Django Enhancement Proposal. A DEP is a design document
providing information to the Django community, or describing a new feature
or process for Django. DEPs provide concise technical specifications of
features, along with rationales.

We intend DEPs to be the primary mechanisms for proposing major new features,
for collecting community input on issues, and for documenting design
decisions that have gone into Django.

The concept and implementation of DEPs (and this document itself!) is a nearly
direct copy of `Python's PEP process <https://www.python.org/dev/peps/>`_ . If
you're already familiar with PEPs, you should be able to quickly grok DEPs by
reading the `differences between DEPs and PEPs`_.

DEP Types
=========

There are three kinds of DEPs:

1. A **Feature** DEP describes a new feature or implementation
   for Django. Most DEPs will be Feature DEPs.

2. An **Informational** DEP describes a Django design issue, or
   provides general guidelines or information to the Django community,
   but does not propose a new feature. Informational DEPs do not
   necessarily represent a community consensus or
   recommendation, so users and implementers are free to ignore
   Informational DEPs or follow their advice.

3. A **Process** DEP describes a process surrounding Django, or
   proposes a change to (or an event in) a process.  Process DEPs are
   like Feature DEPs but apply to areas other than the Django
   framework itself.  They may propose an implementation, but not to
   Django's codebase; they often require community consensus; unlike
   Informational DEPs, they are more than recommendations, and users
   are typically not free to ignore them.  Examples include
   procedures, guidelines, changes to the decision-making process, and
   changes to the tools or environment used in Django development.
   Any meta-DEP is also considered a Process DEP. (So this document
   is a Process DEP).

DEP submission workflow
=======================

So, you'd like to submit a DEP? Here's how it works, and what to expect.

There are several references in this DEP to the **Steering Council**. This
refers to Django's `Steering Council
<https://docs.djangoproject.com/en/dev/internals/organization/#steering-council>`_,
the group of experienced and active contributors who steer technical choices.
Django's documentation lists `the current Steering Council membership
<https://www.djangoproject.com/foundation/teams/#steering-council-team>`_.

At a very high level, the DEP submission process looks like this:

1. `Pre-proposal`_ — someone has an idea and starts collecting early input and
   feedback to see if it's worth writing a DEP.

2. `Forming the team`_ — the DEP author rounds up the help they'll need to get
   the DEP considered.

3. `Submitting the draft`_ — the DEP author writes a rough draft of the DEP and
   submits it via pull request.

4. `Discussion, development, and updates`_ — the DEP and reference
   implementation are discussed, improved, and updated as feedback comes in.

5. `Review & Resolution`_ — the DEP is reviewed by the Steering Council and
   either accepted or rejected.

6. `Implementation`_ — the implementation of the proposed feature is completed
   by the DEP team.

For details on each step, read on.

Pre-proposal
------------

The DEP process begins with a new idea for Django.  It is highly recommended
that a single DEP contain a single key proposal or new idea. Small enhancements
or patches usually don't need a DEP and follow Django's normal `contribution
process <https://docs.djangoproject.com/en/dev/internals/contributing/>`_.

The more focused the DEP, the more successful it tends to be.  The Steering
Council reserve the right to reject DEP proposals if they appear too unfocused
or too broad.  If in doubt, split your DEP into several well-focused ones.

The DEP Author (see below for the formal definition of an Author)
should first attempt to ascertain whether the idea is DEP-able.  Posting to
`django-developers <https://docs.djangoproject.com/en/dev/internals/mailing-
lists /#django-developers-mailing-list>`_ is the best way to go about this.

Vetting an idea publicly before going as far as writing a DEP is meant to save
the potential author time. Many ideas have been brought forward for changing
Django that have been rejected for various reasons. Asking the Django community
first if an idea is original helps prevent too much time being spent on
something that is guaranteed to be rejected based on prior discussions
(searching the Internet does not always do the trick). It also helps to make
sure the idea is applicable to the entire community and not just the author.
Just because an idea sounds good to the author does not mean it will work for
most people in most areas where Django is used.

Forming the team
----------------

Once a DEP has been roughly validated, the author needs to fill out three vital
roles. These roles will be required to get a DEP read, approved, and the code
developed, so you need to identify up-front who will do what. These roles are:

Author
    The **Author** writes the DEP using the style and format described below
    (see `DEP format`_), shepherds the discussions in the appropriate forums,
    and attempts to build community consensus around the idea.

Implementation Team
    The **Implementation Team** are the people (or single person) who will
    actually implement the thing being proposed. A DEP may have multiple
    implementers (and the best DEPs probably will).

    Feature DEPs must have an implementation team to be submitted. Informational
    DEPs generally don't have implementers, and Process DEPs sometimes will.

Shepherd
    If a DEP is being written by someone relatively new to the Django community,
    they will likely need a **Shepherd** -- a mentor, essentially -- to help. The Shepherd
    can be someone with a long history of contributing to Django, who can help
    the Author assess the fitness of their proposal and help make sure it gets
    accepted. The primary job of the Shepherd will be to review the DEP in an
    editorial role, and help guide the Author through the DEP process. 
    
    The Shepherd may be a `Merger`_, and if so the Shepherd will be the one who
    actually merges the code into the project. Or, the Shepherd may be a
    member of the Steering Council, which can help streamline discussion.

    DEPs don't necessarily require a Shepherd, but it's a good idea, especially
    for newer contributors.

.. _merger: https://docs.djangoproject.com/en/dev/internals/organization/#mergers

It's normal for a single person to fulfill multiple roles -- in most cases the
Author will be an/the Implementer, and it's not uncommon for the implementation
team to include the Shepherd as well. It's unusual but acceptable for a single
person to fulfill all roles, though this generally only happens when that person
is a long-time contributor.

Submitting the draft
--------------------

Once the idea's been vetted and the roles are filled, a draft DEP should be
presented to the Django Forum and/or django-developers. This gives the author a
chance to flesh out the draft DEP to make sure it's properly formatted, of high
quality, and to address initial concerns about the proposal.

Following the discussion, the proposal should be sent as a GitHub pull request
to the `django/deps <https://github.com/django/deps>`_ repo. This PR should add
a DEP to the ``drafts/`` directory, written in the style described below. The
draft must be written in DEP style; if it isn't, the pull request may be rejected
until proper formatting rules are followed.

At this point, contributors will review the pull request. In most cases the reviewer
will be the Shepherd of the DEP, but if that's not possible for some reason the
author may want to ask on django-developers and/or the Django Forum to ensure
that this review happens quickly. A reviewer will do the following:

* Read the DEP to check if it is ready: sound and complete.  The ideas
  must make technical sense, even if they don't seem likely to be
  accepted.

* Make sure the title accurately describes the content.

* Check the DEP for language (spelling, grammar, sentence structure,
  etc.), markup, and code style (examples should match PEP 8).

If the DEP isn't ready, the reviewer can leave comments on the pull request,
asking for further revisions. If the DEP's really in bad form, the reviewer
may reject the pull request outright and ask the author to submit a new one
once the problems have been fixed.

The reviewer doesn't pass judgment on DEPs.  They merely do the administrative &
editorial part (which is generally a low volume task).

Once the DEP is ready for the repository, the reviewer will:

* Merge the pull request.

* Assign a DEP number (almost always just the next available number), and rename
  the DEP file with the new number (e.g. rename ``dep-process.rst`` to 
  ``0001-dep-process.rst``)

Developers with commit access to the DEPs repo may create drafts directly by
committing and pushing a new DEP. However, when doing so they need to take on
the tasks normally handled by the reviewer described above. This includes
ensuring the initial version meets the expected standards for submitting a DEP.
Of course, committers may still choose to submit DEPs as a pull request to
benefit from peer review.

Discussion, development, and updates
------------------------------------

At this point there will generally be more discussion, modifications to the
reference implementation, and of course updates to the DEP. It's rare for
a DEP to be judged on the first draft; far more common is several rounds
of feedback and updates.

Updates to a DEP can be submitted as pull requests; once again, someone with
merge access to the DEP repo will merge those pull requests (typically they
don't require much if any review). In cases where the Author has commit access
the Author should just update the draft DEP directly.

Feature DEPs generally consist of two parts, a design document and a
reference implementation.  It is generally recommended that at least a
prototype implementation be co-developed with the DEP, as ideas that sound
good in principle sometimes turn out to be impractical when subjected to the
test of implementation.

DEP authors are responsible for collecting community feedback on a DEP
before submitting it for review. However, wherever possible, long
open-ended discussions on public mailing lists should be avoided.
Strategies to keep the discussions efficient include: setting up a
separate mailing list for the topic, having the DEP author accept
private comments in the early design phases, setting up a wiki page, etc.
DEP authors should use their discretion here.

Review & Resolution
-------------------

Once the author has completed a DEP, the Author or Shepherd will ask the
Steering Council for review and pronouncement. The final authority for deciding
on a DEP rests with the Steering Council. They may choose to rule on a DEP as a
team, or they may designate one or more members to review and decide.

Having the Shepherd (i.e. an experienced contributor) rather than the Author ask
helps ensure that the DEP meets the basic technical bar before it's called for
review. It also provides a fairly strong fitness test before the Steering
Council is asked to rule on it, making rulings fairly easy. If the Shepherd is
happy, the Steering Council will likely be as well.

For a DEP to be accepted it must meet certain minimum criteria.  It must be a
clear and complete description of the proposed enhancement. The enhancement must
represent a net improvement. The proposed implementation, if applicable, must be
solid and must not complicate Django unduly. Finally, a proposed enhancement
must "fit" with Django's general philosophy and architecture. This last category
is the most imprecise and takes the most judgment, so if the Steering Council
rejects a DEP for lack of "fit" they should provide a clear explanation for why.

At this point, the DEP will be considered "Accepted" and moved to the
``accepted`` directory in the DEPs repo.

A DEP can also be "Withdrawn".  The DEP Author or maintainer of the DEPs repo
can assign the DEP this status when the Author is no longer interested in the
DEP, or if no progress is being made on the DEP.  Once a DEP is withdrawn, it's
moved to the ``withdrawn`` directory for reference. Later, another author may
resurrect the DEP by opening a pull request, updating (at least) the author, and
moving it back to ``draft``.

Finally, a DEP can also be "Rejected".  Perhaps after all is said and done it
was not a good idea.  It is still important to have a record of this
fact. Rejected DEPs will be moved to the ``rejected`` directory, and
generally should be updated with a rationale for rejection.

DEPs can also be superseded by a different DEP, rendering the original
obsolete.  This is intended for Informational DEPs, where version 2 of
an API can replace version 1.

Implementation
--------------

Finally, once a DEP has been accepted, the implementation must be completed. In
many cases some (or all) implementation will actually happen during the DEP
process: Feature DEPs will often have fairly complete implementations before
being reviewed by the Steering Council. When the implementation is complete and
incorporated into the main source code repository, the status will be changed to
"Final" and the DEP moved to the ``final`` directory.

DEP format
==========

To save everyone time reading DEPs, they need to follow a common format
and outline; this section describes that format. In most cases, it's probably
easiest to start with copying one of the provided DEP templates
(`rst template <../template.rst>` - `md template <../template.md>`)_,
and filling it in as you go. 

DEPs may be written in `reStructuredText <http://docutils.sourceforge.net/rst.html>`_ 
(the same format as Django's documentation) or
`Markdown <https://www.markdownguide.org>`_ (the same as GitHub issues). 

Each DEP should have the following parts:

#. A short descriptive title (e.g. "ORM expressions"), which is also reflected
   in the DEP's filename (e.g. ``0181-orm-expressions.rst``).

#. A preamble --  containing metadata about the DEP, including the DEP number,
   the names of the various members of the `DEP team <#forming- the-team>`_, and so forth.
   See `DEP Metadata`_ below for specific details.
   This can be provided as a rST `field list <http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#field-lists>`_
   or `Markdown frontmatter <https://github.com/Kernix13/markdown-cheatsheet/blob/master/frontmatter.md>`_
   depending on which template you are using.

#. Abstract -- a short (~200 word) description of the technical issue
   being addressed.

#. Specification -- The technical specification should describe the syntax and
   semantics of any new feature.  The specification should be detailed enough to
   allow implementation -- that is, developers other than the author should
   (given the right experience) be able to independently implement the feature,
   given only the DEP.

#. Motivation -- The motivation is critical for DEPs that want to add
   substantial new features or materially refactor existing ones.  It should
   clearly explain why the existing solutions are inadequate to address the
   problem that the DEP solves.  DEP submissions without sufficient motivation
   may be rejected outright.

#. Rationale -- The rationale fleshes out the specification by describing what
   motivated the design and why particular design decisions were made.  It
   should describe alternate designs that were considered and related work.

   The rationale should provide evidence of consensus within the community and
   discuss important objections or concerns raised during discussion.

#. Backwards Compatibility -- All DEPs that introduce backwards
   incompatibilities must include a section describing these incompatibilities
   and their severity.  The DEP must explain how the author proposes to deal
   with these incompatibilities.  DEP submissions without a sufficient backwards
   compatibility treatise may be rejected outright.

#. Reference Implementation -- The reference implementation must be completed
   before any DEP is given status "Final", but it need not be completed before
   the DEP is accepted.  While there is merit to the approach of reaching
   consensus on the specification and rationale before writing code, the
   principle of "rough consensus and running code" is still useful when it comes
   to resolving many discussions of API details.

   The final implementation must include tests and documentation, per Django's
   `contribution guidelines <https://docs.djangoproject.com/en/dev/internals/contributing/>`_.

#. Copyright/public domain -- Each DEP must be explicitly licensed
   as `CC0 <https://creativecommons.org/publicdomain/zero/1.0/>`_.

DEP Metadata
------------

Each DEP must begin with some metadata given as an rST 
`field list <http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#field-lists>`_. 
The headers must contain the following fields:

``DEP``
    The DEP number. In an initial pull request, this can be left out or given
    as ``XXXX``; the reviewer who merges the pull request will assign the DEP
    number.
``Type``
    ``Feature``, ``Informational``, or ``Process``
``Status``
    ``Draft``, ``Accepted``, ``Rejected``, ``Withdrawn``, ``Final``, or ``Superseded``
``Created``
    Original creation date of the DEP (in ``yyyy-mm-dd`` format)
``Last-Modified``
    Date the DEP was last modified (in ``yyyy-mm-dd`` format)
``Author``
    The DEP's author(s).
``Implementation-Team``
    The person/people who have committed to implementing this DEP
``Shepherd``
    A more experienced developer to help mentor and guide the DEP forward
``Requires``
    If this DEP depends on another DEP being implemented first,
    this should be a link to the required DEP.
``Django-Version`` (optional)
    For Feature DEPs, the version of Django (e.g. ``1.8``) that this
    feature will be released in.
``Replaces`` and ``Superseded-By`` (optional)
    These fields indicate that a DEP has been rendered obsolete. The newer DEP
    must have a ``Replaces`` header containing the number of the DEP that it
    rendered obsolete; the older DEP has a ``Superseded-By`` header pointing to
    the newer DEP.
``Resolution`` (optional)
    For DEPs that have been decided upon, this can be a link to the final
    rationale for acceptance/rejection. It's also reasonable to simply update
    the DEP with a "Resolution" section, in which case this header can be left
    out.

Auxiliary Files
---------------

DEPs may include auxiliary files such as diagrams.  Such files must be named
``XXXX-descriptive-title.ext``, where "XXXX" is the DEP number, 
"descriptive-title" is a short slug indicating what the file contains, and 
"ext" is replaced by the actual file extension (e.g. "png").

Reporting DEP Bugs, or Submitting DEP Updates
=============================================

How you report a bug, or submit a DEP update depends on several factors, such as
the maturity of the DEP, the preferences of the DEP author, and the nature of
your comments.  For the early draft stages of the DEP, it's probably best to
send your comments and changes directly to the DEP author.  For more mature, or
finished DEPs you can submit corrections as GitHub issues or pull requests
against the DEP repository.

When in doubt about where to send your changes, please check first with the DEP
author and/or the Steering Council.

DEP authors with git push privileges for the DEP repository can update the DEPs
themselves.

Transferring DEP Ownership
==========================

It occasionally becomes necessary to transfer ownership of DEPs to a new author.
In general, it is preferable to retain the original author as a co-author of the
transferred DEP, but that's really up to the original author.  A good reason to
transfer ownership is because the original author no longer has the time or
interest in updating it or following through with the DEP process, or has fallen
off the face of the 'net (i.e. is unreachable or not responding to email).  A
bad reason to transfer ownership is because the new author doesn't agree with
the direction of the DEP. One aim of the DEP process is to try to build
consensus around a DEP, but if that's not possible, an author can always submit
a competing DEP.

If you are interested in assuming ownership of a DEP, first try to contact the
original author and ask for permission. If they approve, ask them to open a pull
request transferring the DEP to you. If the original author doesn't respond to
email within a few weeks, contact django-developers.


Differences between DEPs and PEPs
=================================

.. note::

    This section is historical, describing the differences between the DEP and
    PEP processes when this was originally written in 2014. Since then, the PEP
    process has changed -- in particular, there's now a Python Steering Council,
    and a mechanism for delegating authority for each specific PEP. This section
    hasn't been updated to reflect those changes, nor the changes to the DEP
    process either.

As stated in the preamble, the DEP process is more or less a direct copy of
the PEP process (and this document is a modified version of 
`PEP 1 <https://www.python.org/dev/peps/pep-0001/>`_). 

Relative to the PEP process, we made the following changes in DEPs:

- The workflow is GitHub based (rather than email-based as in PEP 1).

  This is a simple enough change, but has a number of ramifications for the
  details of how DEPs work, including:

  - DEPs use pull requests (and direct commits) as the workflow process.
  - DEPs use rST-style headers rather than RFC822 (because rST-style headers
    render properly on GitHub without additional tooling).
  - DEPs have document titles rather than title fields in the metadata
    (again, because of GitHub rendering).
  - DEPs are organized into directories based on statuses (e.g. ``draft/``,
    ``accepted/``, ``final/``, etc) so that additional tooling to create an
    index by status isn't needed.
  - DEP file names are more descriptive (e.g. ``0181-orm-expressions.rst``),
    again to avoid the need for additional tooling.
  - DEPs are "edited" (e.g. pull request approved) by any core developer,
    rather than an explicit "editor" role like the PEP editors.

- DEPs are pronounced upon by the Steering Council, rather than a BDFL (because
  Django no longer has BDFLs).

- DEPs explicitly require identifying a few roles (Author, Implementation Team,
  and Shepherd) before submission and throughout the process. With PEPs, most
  are authored and implemented by the same person, but the same doesn't seem to
  be true of DEPs (so far), hence the "implementer" role. As for the "shepherd":
  the BDFL or BDFL-delegate tends to be much more hands-on than the Technical
  Board, so the role of commenting and critiquing will be fulfilled by the
  shepherd, rather than the board. Further, we've observed that features are
  tremendously unlikely to make it into Django without a committer on board to
  do the detail-work of merging a patch.

- DEPs simplify the metadata somewhat, removing a few fields ("Post-History",
  etc.) and dropping a couple of statuses ("Active" gets merged into "Final",
  and "Deferred" merged into "Withdrawn").

- DEPs have "Feature DEPs" rather than "Standards Track" DEPs.

- DEPs may only be reStructuredText (there is no plain text option).

Revision History
================

2023-10-23
    Updates to reflect changes in governance since this document was originally
    written, including changes from "Technical Board" to "Steering Council",
    the removal of the no-longer-existant "Core Developer" concept, and updates
    to reflect the Merger role.

2014-04-14
    Initial version

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (https://creativecommons.org/publicdomain/zero/1.0/deed).
