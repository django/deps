==============================
DEP XXXX: Experimental APIs
==============================

:DEP: XXXX
:Author: Andrew Miller, Praful Gulani
:Implementation Team: Andrew Miller, Praful Gulani
:Shepherd: Andrew Miller
:Status: Draft
:Type: Process
:Created: 2026-06-08
:Replaces: `DEP 2 <https://github.com/django/deps/blob/main/draft/0002-experimental-apis.rst>`_.

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

This DEP proposes a formal process for introducing "Experimental" features and 
APIs into Django. Currently, Django operates on an all-or-nothing model: features 
are either hidden and undocumented, or fully public and locked into a strict, 
multi-year stability guarantee. While this approach ensures that official releases 
are exceptionally stable, it struggles when features carry a unique set of challenges.
Challenges like API design deadlocks, partial implementations that need to land 
incrementally, or updates to core systems like auth.User that lead to breaking 
changes, require an alternate approach.

This proposal creates an isolated space for the features to evolve under 
real-world usage and feedback, all while keeping production environments safe from 
accidental instability. Features in this space will be fully documented so they 
are visible to the community, but they will remain explicitly exempt from standard
backwards-compatibility policy until they mature.

Motivation
==========

Django values stability and strict backwards compatibility the most.
Under the current policy, the moment a new feature is documented and released, it is 
locked into a multi-year deprecation cycle. Because of this, the community needs 
absolute design perfection before code can be merged. While this approach works 
great and is the reason behind Django's stability, it has also led to prolonged 
debates for some features which has caused some valuable contributions to lose momentum.

The current methods to bring new features into Django work fine most of the time.
However, when a contribution introduces a complex change, it can be difficult to 
make progress using current approaches. The new experimental path serves as an 
alternate option specifically for scenarios where the existing methods face limitations:

1. Third-Party Packages
-----------------------
Third-party packages work great for adding new features or tools. However, when a feature
fundamentally changes Django's internal mechanics or early startup steps, an alternate
approach is needed to test those changes safely.

We see this in `Ticket-24312 (making it possible to import models safely at any time) <https://code.djangoproject.com/ticket/24312>`_.
Rewriting Django’s app-loading system to remove its reliance on import side 
effects is a massive architectural shift. A third-party package cannot solve 
this because it is bound by the very loading system it tries to fix. An experimental 
namespace provides a safe playground to map out what the final design of such a 
core refactor looks like without breaking stable production environments.

2. Merging Directly into Core
-----------------------------
Django requires wide compatibility across all supported backends and 
environments before code is merged into the main codebase. However, demanding 
simultaneous perfection across every single environment on day one can sometimes
delay mature parts of a feature from being integrated. Furthermore, attempting 
to land massive changes all at once places a very heavy burden on both code 
submitters and reviewers.

We see this in `Ticket-28805 (adding database functions for regular expressions) <https://code.djangoproject.com/ticket/28805>`_. 
While implementations for some database backends were ready, the feature stalled for 
years because core integration required simultaneous support across every single 
environment. An experimental space would allow ready components to land, letting the 
community use those features while the remaining database compatibility issues are
resolved over subsequent releases.

3. Undocumented Features
------------------------
Maintainers sometimes choose not to document temporary extension points or core 
refactors because the design is not yet stable enough for a permanent public 
commitment. While this successfully protects production environments from breaking
changes, it naturally limits community awareness. Without documentation, only a 
small group of developers ever discover them and provide feedback.

An Experimental Space
---------------------

This DEP introduces an "Experimental" space to create a safe, native pathway to 
improve framework features. By letting code land without immediate, permanent 
stability promises, maintainers get the flexibility to iterate on complex designs 
based on real-world usage and feedback.

This isolated space will also allow us to safely evolve existing 
core systems. It provides a safe zone to experiment with modernizing critical, 
long-standing framework components without breaking existing projects. For example, 
`updating auth.User <https://buttondown.com/carlton/archive/evolving-djangos-authuser/>`_ 
to replace the ``first_name`` and ``last_name`` fields with a singular ``name`` field, 
or making the email unique, becomes possible because the community can natively test 
the changes before they are made permanent.

By having this isolation space, we wouldn’t have to change Django’s policy regarding 
undocumented features. Instead, by bringing unstable components under the experimental
space, we can safely document them and provide a direct link to a dedicated forum
discussion where all the feedback can be gathered.

The Experimental Feature Pipeline
=================================

This framework integrates directly into the workflow managed via the django/new-features 
repository to govern the lifecycle of an experimental feature.

1. Community Support Check:
   Every feature begins with a proposal in the django/new-features repository 
   to gather initial community feedback and see if the idea belongs in Django core.

2. Selecting the Experimental Path:
   During the "Can we do it?" phase, if the Steering Council decides that a feature 
   is too complex to merge as a stable release immediately either due to high 
   compatibility risks or the need for multi-database testing, they can choose the
   experimental pathway.

3. The Proposal and Contract:
   The author submits a detailed proposal following the standard new-features guidelines. 
   This draft must include a clear plan outlining the specific testing goals, a realistic 
   timeline, and clear criteria for when the feature should either be made permanent 
   or completely removed.

4. Merging and Testing:
   Once approved by the Steering Council, a Trac ticket is created and the code is 
   merged into the main Django repository behind a safe experimental namespace. The 
   community can then test the feature and provide feedback based on the goals outlined 
   in the original plan.

Ecosystem Marketing and Feedback Mechanics
==========================================

To prevent experimental features from becoming invisible tools that only a few advanced
developers notice, Django will use a clear communication strategy to invite active user 
testing and feedback:

*  **Release Notes Section:** Every feature release will have a highly visible section 
   right at the top listing all active experimental modules and extension points 
   included in that release.

*  **Documenting What is Missing:** Documentation for experimental components must not 
   just state how the feature works, it should also explicitly list what is currently 
   missing or incomplete, so users know exactly where to focus their testing efforts.

*  **Direct Links for Forum Feedback:** Every experimental documentation block will 
   include a direct link pointing to a dedicated feedback thread on the Django Forum. 
   This ensures all user experiences, bug reports, and design suggestions are collected 
   in one place.
	 
Specification
=============

This section should contain a complete, detailed technical specification which
should describe the syntax and semantics of any new feature. The specification
should be detailed enough to allow implementation -- that is, developers other
than the author should (given the right experience) be able to independently
implement the feature, given only the DEP.

Rationale
=========

This section should flesh out out the specification by describing what motivated
the specific design and why particular design decisions were made.  It
should describe alternate designs that were considered and related work.

The rationale should provide evidence of consensus within the community and
discuss important objections or concerns raised during discussion.

Reference Implementation
========================

If there's an implementation of the feature under discussion in this DEP,
this section should include or link to that implementation and provide any
notes about installing/using/trying out the implementation.

Backwards Compatibility
=======================

Features designated as "Experimental" under this framework will be explicitly 
exempt from Django's standard multi-release deprecation cycle. Because this 
framework must seamlessly integrate with the annual release cycle established in 
DEP 20, the exact rules governing the lifecycle of an experiment remain open.

  **TODO:** This section will be articulated following community feedback on the Django Forum. 


Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).

(All DEPs must include this exact copyright statement.)