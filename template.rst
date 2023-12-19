======================
DEP XXXX: DEP template
======================

:DEP: XXXX
:Author: Jacob Kaplan-Moss
:Implementation Team: Jacob Kaplan-Moss
:Shepherd: Andrew Godwin, Carl Meyer
:Status: Draft
:Type: Feature
:Created: 2014-11-16
:Last-Modified: 2014-11-18

.. contents:: Table of Contents
   :depth: 3
   :local:

This DEP provides a sample template for creating your own DEPs.  In conjunction
with the content guidelines in `DEP 1 <https://github.com/django/deps/final/0001-dep-process.rst>`_,
this should make it easy for you to conform your own DEPs to the format
outlined below.

Note: if you are reading this DEP via the web, you should first grab `the source
of this DEP <https://raw.githubusercontent.com/django/deps/template.rst>`_ in
order to complete the steps below.  **DO NOT USE THE HTML FILE AS YOUR
TEMPLATE!**

To get the source this (or any) DEP, look at the top of the Github page
and click "raw".

If you're unfamiliar with reStructuredText (the format required of DEPs),
see these resources:

* `A ReStructuredText Primer`__, a gentle introduction.
* `Quick reStructuredText`__, a users' quick reference.
* `reStructuredText Markup Specification`__, the final authority.

__ http://docutils.sourceforge.net/docs/rst/quickstart.html
__ http://docutils.sourceforge.net/docs/rst/quickref.html
__ http://docutils.sourceforge.net/spec/rst/reStructuredText.html

Once you've made a copy of this template, remove this abstract, fill out the
metadata above and the sections below, then submit the DEP. Follow the 
guidelines in `DEP 1 <https://github.com/django/deps/final/0001-dep-process.rst>`_.

Abstract
========

This should be a short (~200 word) description of the technical issue being
addressed.

This (and the above metadata) is the only section strictly required to submit a
draft DEP; the following sections can be barebones and fleshed out as you work
through the DEP process.

Specification
=============

This section should contain a complete, detailed technical specification which
should describe the syntax and semantics of any new feature. The specification
should be detailed enough to allow implementation -- that is, developers other
than the author should (given the right experience) be able to independently
implement the feature, given only the DEP.

Motivation
==========

This section should explain *why* this DEP is needed. The motivation is critical
for DEPs that want to add substantial new features or materially refactor
existing ones.  It should clearly explain why the existing solutions are
inadequate to address the problem that the DEP solves.  DEP submissions without
sufficient motivation may be rejected outright.

Rationale
=========

This section should flesh out out the specification by describing what motivated
the specific design and why particular design decisions were made.  It
should describe alternate designs that were considered and related work.

The rationale should provide evidence of consensus within the community and
discuss important objections or concerns raised during discussion.

Backwards Compatibility
=======================

If this DEP introduces backwards incompatibilities, you must must include this
section. It should describe these incompatibilities and their severity, and what
mitigation you plan to take to deal with these incompatibilities.

Reference Implementation
========================

If there's an implementation of the feature under discussion in this DEP,
this section should include or link to that implementation and provide any
notes about installing/using/trying out the implementation.

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).

(All DEPs must include this exact copyright statement.)
