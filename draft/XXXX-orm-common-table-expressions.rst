=========================================================
DEP XXXX: Common Table Expressions in the Django ORM
=========================================================

:DEP: XXXX
:Author: Genaro Camele
:Implementation Team: Genaro Camele
:Shepherd: -
:Status: Draft
:Type: Feature
:Created: 2026-01-03

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

This DEP proposes first-class Common Table Expression (CTE) support in Django's
ORM, with an automatic optimization strategy as the primary behavior and an
explicit API for advanced use cases. The implementation is already available in
`PR #20713 <https://github.com/django/django/pull/20713>`_ (previously
`PR #20655 <https://github.com/django/django/pull/20655>`_).
This DEP is based on those PRs.

The feature addresses repeated subquery evaluation and annotation duplication in
complex ORM queries by lifting eligible subqueries and annotation chains into
CTEs during query compilation. This preserves ORM expressiveness while reducing
duplicated SQL work and improving database execution plans in many real-world
cases.

Benchmarks included in the above PRs (with detailed scenarios and results)
show performance improvements for complex query shapes, especially where
correlated aggregate subqueries or deeply reused annotations are involved.

The proposal is designed for interoperability with current `django-cte <https://github.com/dimagi/django-cte>`_
(`docs <https://dimagi.github.io/django-cte/>`_)
usage, allowing users to choose between built-in CTE support and the
third-party library without forcing immediate migration.

Specification
=============

Overview
--------

The ORM will support CTEs through two complementary paths:

1. Automatic CTE rewriting.
2. Explicit CTE construction API.

The preferred behavior, and the one selected when implementation proposals
compete, is automatic rewriting. Users should not be required to manually adopt
a new API to benefit from CTE-based query planning improvements.

Automatic CTE Rewriting (Primary)
---------------------------------

Before SQL generation, query compilation applies an automatic CTE
transformation pass. The pass:

1. Collects eligible subqueries and repeated expression chains.
2. Materializes them as named CTEs.
3. Rewrites expressions to reference CTE columns.
4. Emits a ``WITH RECURSIVE ...`` clause containing only CTEs actually used by
   the final SQL.

The auto-rewrite currently targets:

1. Correlated aggregate subqueries that can be converted into grouped CTE joins.
2. Dependent annotation chains that would otherwise duplicate expressions.
3. Repeated non-correlated subquery expressions suitable for one-time
   materialization and reuse.

Safety checks prevent rewriting when semantics could change (for example:
queries with outer references, unsupported slicing patterns, or other shapes
that are not provably equivalent).

Explicit CTE API
----------------

The public ORM API includes:

.. code-block:: python

   from django.db.models import CTE, with_cte

   cte = CTE(queryset, name="my_cte", materialized=False)
   qs = with_cte(cte, select=cte.join(MyModel, field=cte.col.some_field))

Capabilities:

1. Named CTEs.
2. ``CTE.recursive(...)`` for recursive CTE definitions.
3. ``materialized=True`` for backends that support ``AS MATERIALIZED``.
4. Column references via ``cte.col.<column_name>``.
5. Join composition via ``cte.join(...)``.

SQL Generation and Compiler Integration
---------------------------------------

CTE generation is integrated into SQL compilers so that:

1. Auto-rewrite runs before SQL assembly.
2. CTE SQL is prepended once (avoiding duplicate wrapping).
3. ``EXPLAIN`` remains outside the ``WITH`` clause.
4. Only referenced CTEs are emitted, including dependencies between CTEs.

Interoperability with ``django-cte``
------------------------------------

Interoperability is a requirement of this DEP:

1. The implementation accepts compatible join objects and compiler behaviors.
2. Built-in CTE support and ``django-cte`` can coexist in a single query
   construction flow.
3. Existing explicit patterns are preserved so users can choose either
   implementation without migration friction.

Motivation
==========

Complex ORM queries often repeat expensive SQL fragments:

1. Correlated ``Subquery()`` aggregates repeated in annotations and filters.
2. Annotation chains where later expressions depend on earlier computed aliases.
3. Reused scalar subqueries across select, filter, and ordering clauses.

These patterns can produce large SQL, repeated scans, and less predictable
planner behavior, especially at scale.

CTEs solve this by letting the database compute reusable intermediate results
once and reference them multiple times. The PR benchmarks document this effect
in depth and show clear improvements in relevant workloads.

The accepted ticket for this feature indicates community agreement on the need.
This DEP defines the architecture and product direction needed for Steering
Council review and acceptance.

Rationale
=========

Why Automatic CTE Rewriting Is the Preferred Proposal
-----------------------------------------------------

Automatic rewriting is selected as the primary design because it:

1. Improves performance without requiring API adoption work from users.
2. Preserves existing queryset code and mental models.
3. Centralizes optimization policy in ORM internals, where query shape and
   safety checks are already managed.

Manual-only approaches (where users must explicitly define CTEs in application
code to obtain improvements) were considered and are rejected as the primary
direction. They increase user burden and would leave most existing code paths
unoptimized.

Why Keep an Explicit API
------------------------

An explicit API is still valuable for:

1. Recursive queries.
2. Hand-tuned query plans.
3. Advanced SQL composition where intent should be explicit.

This dual approach gives Django strong defaults while preserving expert control.

Licensing and Code Lineage
--------------------------

Parts of the current implementation are derived from ``django-cte`` code under
the BSD 3-Clause License. The codebase includes the corresponding license
header and credits original authors in relevant files.

This is acceptable and intentional in the current proposal because it reduced
time-to-implementation, preserved known behavior, and kept interoperability.

If preferred by project policy, the derived portions could be rewritten from
scratch to avoid any code lineage from ``django-cte``. However, that path would
require additional implementation and validation time and would delay delivery.

Backwards Compatibility
=======================

This is an additive feature. Existing ORM APIs continue to work.

Potential compatibility considerations:

1. Generated SQL text may change shape (e.g., added ``WITH`` blocks), which can
   affect SQL-string assertions in tests.
2. Query plans may change due to CTE materialization/rewriting decisions.
3. Backend-specific behavior for ``AS MATERIALIZED`` remains subject to backend
   support and validation.

The implementation is designed to preserve query semantics and includes guard
conditions to skip rewrites when equivalence is not guaranteed.

Reference Implementation
========================

This DEP is based on:

1. `PR #20713 <https://github.com/django/django/pull/20713>`_
2. `PR #20655 <https://github.com/django/django/pull/20655>`_

Those PRs include:

1. ORM/compiler integration for automatic CTE rewrites.
2. Public ``CTE`` and ``with_cte`` APIs.
3. Recursive and materialized CTE support.
4. Interoperability paths with ``django-cte``.
5. Tests and benchmark scenarios demonstrating performance improvements for
   complex queries.

Before finalization, implementation work must include complete documentation,
full test coverage across supported backends, and any refinements required by
Steering Council feedback.

Acknowledgments
===============

This proposal and implementation build on substantial prior work from the
``django-cte`` project. Credit goes to Dimagi Inc. and the individual
maintainers and contributors of ``django-cte`` who designed, implemented, and
maintained production CTE support that informed this work.

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).
