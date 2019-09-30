========================
DEP 2: Experimental APIs
========================

:DEP: 2
:Author: Andrew Godwin
:Implementation Team: Andrew Godwin
:Shepherd: Andrew Godwin
:Status: Draft
:Type: Process
:Created: 2014-12-05

.. contents:: Table of Contents
   :depth: 3
   :local:


Abstract
========

This DEP outlines a new process for introducing APIs to Django and documenting them
but keeping them outside the usual deprecation and stability cycle, instead marking
them as "Experimental" APIs.

Motivation
==========

Currently, Django has an all-or-nothing policy; that is, features are either
undocumented and thus considered outside of Django's backwards-compatibility
policy and subject to change at any time, or they are documented and considered
stable and subject to the three-release deprecation cycle that Django has.

This limits the ability to introduce APIs and gauge user and developer reactions
to them; a feature must essentially be developed in isolation and perhaps tested
among interested parties, but cannot get wider reach until it lands into Django
proper.

One option in the past was simply not to document it, but this goes against our
policy of features coming with both tests and documentation, and as has been
shown with things like ``Model._meta``, liable to adoption by the community
anyway.

Instead, an Experimental designation will allow APIs to be included in Django
and released without being beholden to the full deprecation cycle. They will
still be included in the security policy and backwards compatibility will
be kept on a best-efforts basis, but not guaranteed. Effort will be taken to
communicate to users that the APIs in question are not stable to avoid
inadvertent use.

Implementation
==============

The implementation of this feature consists purely of documentation describing
the process below, which will be added to the API Stability documentation at
https://docs.djangoproject.com/en/dev/misc/api-stability/ - the current
wording mentioning "Internal" will be reworked to mention "Internal and
Experimental" and the explanations below added.

If a feature is to be marked as experimental it should have documentation
submitted as normal, but a prominent callout should be placed on any
documentation referring to the feature to mark it as experimental (perhaps
via a new Sphinx directive?).

The release notes for the release the feature appears in should have any
experimental features called out in a separate section of the release notes,
similar to the backwards incompatible changes section; effort must be taken
to ensure they are clearly not part of the normal feature set.

Once a feature has been released as stable (i.e. documented and not marked
as experimental) it cannot then be reverted back into experimental state.

Experimental features should not be included in LTS releases. This may be
allowed if the feature was already experimental in the previous release
and is not yet ready to be marked stable or removed.

Experimental features will be kept stable within a major Django release
number (e.g. between 1.7, 1.7.1, 1.7.2) but there are no API guarantees
whatsoever between major versions. Nonetheless, the API should not
suddenly change without reason; to have got as far as an experimental
feature in the main codebase it should have passed a certain quality
threshold and the DEP process and already be somewhat fully-formed.

Experimental features, like all of Django, will be patched and new releases
issued if security holes are found.

Rationale
=========

It might be possible to raise silent warnings if people use experimental
features (similar to the silent ``PendingDeprecationWarning``), but the value
of such a feature to stop people using them unknowingly (if they knew enough
to turn on the warnings, they probably know what's experimental) and the
additional code complexity this results in means it's not considered here.

The note about LTS releases not being allowed to have experimental code is
a soft argument but makes sense; these are meant to represent the most
stable platform of Django, and it seems sensible to keep them as
experiment-free as possible.

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).
