=======================================================
DEP XXXX: Adding Third-Party Packages as Package Extras
=======================================================

:DEP: XXXX
:Author: Praful Gulani, Andrew Miller
:Implementation Team: Praful Gulani, Andrew Miller
:Shepherd: Andrew Miller
:Status: Draft
:Type: Process
:Created: 2026-08-21

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

While Django follows a batteries-included philosophy, including every new 
feature/requirement according to modern application demands would lead to 
bloated core and increased load on maintainers. Using package extras would 
keep Django core lean and would also increase the visibility of high quality 
third-party packages. 

This DEP defines the requirements and testing needed for adding third-party 
packages as "package extras" within the django framework. The installation of 
package extras shouldn’t affect django’s stability and performance and packages 
need to guarantee this by maintaining appropriate isolation and bridging test 
suites for flawless integration. 


Motivation
==========

Django’s batteries included approach makes it a reliable framework for web 
development. But the web ecosystem is huge and as it evolves it can be tough to 
incorporate everything directly into Django core. Trying to give everything out 
of the box can lead to bloated codebase and can increase the burden on maintainers.

Django is also known for its massive and robust third party package ecosystem, 
most django projects use some third-party package for essential functionality. 
A lot of well maintained third-party packages receive the attention they deserve 
but many of them don’t. 

By introducing package extras the whole community gets benefited:
* By not adding everything to the core we can keep the core lean and also allow 
the functionality to be added officially without any maintenance overhead.
* Listing well maintained third-party packages as extras increases their 
visibility for the users and also acts as encouragement for the developers.


Guidelines for third party packages
===================================

* The package must have a documented security policy and a responsive process 
  for reporting vulnerabilities.
* The package must use a license compatible with Django's BSD-3 clause license.
* Top-level ``__init__.py`` files must not perform eager network calls, heavy 
  IO, or database access.
* The package must follow a deprecation schedule aligned with Django's releases.
* Packages must use lower-bound constraints (``package>=X.Y``) rather than exact 
  versions (``package==X.Y.Z``) for declaring Django dependency.
* Third-party packages that rely on private Django APIs must run CI matrix 
  checks against ``django/main``.


Specification
=============

Listing package extras without a proper process introduces significant risks:
* Some third-party packages might alter global settings with a simple install 
before being configured in ``settings.py``
* Poorly specified or circular third-party dependencies can break installations 
across package managers.
* Unconfigured extras executing early imports might lead to performance degradations.

To safely list package extras without compromising the stability and performance 
of Django we need to have a test suite that helps with isolation and bridging 
of the packages.


Rationale
=========

This section should flesh out the specification by describing what motivated 
the specific design and why particular design decisions were made. It should 
describe alternate designs that were considered and related work.
The rationale should provide evidence of consensus within the community and 
discuss important objections or concerns raised during discussion.


Backwards Compatibility
=======================

This DEP doesn't introduce any backwards incompatibilities. It does not modify 
any of the existing django applications.


Copyright
=========

This document has been placed in the public domain per the Creative Commons 
CC0 1.0 Universal license (https://creativecommons.org/publicdomain/zero/1.0/deed).