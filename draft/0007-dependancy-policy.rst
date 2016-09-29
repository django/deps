========================
DEP 7: Dependency Policy
========================

:DEP: 7
:Author: Jacob Kaplan-Moss
:Implementation Team: Jacob Kaplan-Moss
:Shepherd: Jacob Kaplan-Moss
:Status: Draft
:Type: Process
:Created: 2016-06-06
:Last-Modified: 2016-09-29

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

This DEP outlines Django's policy on external dependencies (e.g. other Python
packages required to run Django). It supersedes Django's previous, unspoken
policy of "no external dependencies allowed."

In a nutshell, the policy is that adding a new external dependency should be
treated similarly to adding a new feature to Django: it requires a demonstration
that the dependency is needed, and rough consensus among the community and core
team that the chosen dependency is the correct one. If the dependency is
controversial, it may require a DEP and a decision by the Technical Board.

The rest of this document explains some background and motivation to this
policy, and outlines in more details the guidelines on determining if a new
dependency is acceptable.

Motivation
==========

- "python packaging is good now"
- it's time
- vendored stuff is a pain
- bcrypt, etc

Specification
=============

Guidelines for adding new dependencies
--------------------------------------

- External dependencies should be easy to install on all the platforms that Django supports (i.e. Linux/Mac/Windows, all supported Python versions including PyPy, etc). This means that dependencies that require C extensions are probably not acceptable.
- stability
- maintainability
- "backup plan"
- requires a short DEP for a new dep, ruling by core team as usual
    - ??? accelerated mini-DEP for this?

Optional dependencies
---------------------

- optional deps are ok too, less stringent guidelines

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).

(All DEPs must include this exact copyright statement.)