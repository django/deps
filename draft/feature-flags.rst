==================================
DEP XXXX: Feature Flags Framework
==================================

:DEP: XXXX
:Author: Praful Gulani, Andrew Miller
:Implementation Team: Praful Gulani, Andrew Miller
:Shepherd: Andrew Miller
:Status: Draft
:Type: Feature
:Created: 2026-08-21

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

Currently, Django does not have a built-in feature flag system. Developers either 
need to build custom setups, or rely on third-party packages with technical and 
functional limitations, or use paid third-party services.

This DEP proposes adding a feature flag framework to Django. Feature flags allow 
developers to turn features on or off safely in production without redeploying 
code. The framework will have a unified API design which will support pluggable 
storage backends, flexible targeting rules using logical operators, deterministic 
hashing for consistent rollouts along with safe testing, and kill-switch 
capabilities to safely roll back breaking changes.


Motivation
==========

Feature flags are an important part of development. They allow dark launches, 
users/groups/location based deployments, A/B testing, and kill-switch 
capabilities without requiring code redeployments.

Currently, Django lacks feature flags and developers have to choose between these 
three approaches:

1. Custom Implementations: Developers frequently implement custom, boolean checks 
using Django settings, environment variables, or custom database models. These 
implementations often lack standard methods for targeting users, analyzing metrics, 
gradual rollout, or proper fallbacks, leading to fragmented code patterns across 
different apps in a Django application for every new feature that needs to be tried out.

2. Third-Party Packages: While several third-party packages exist, they vary 
significantly in API design, maintenance frequency, backend support, and 
compatibility with modern Django features. Those packages rely heavily on Django's 
request object for flag evaluation. But flags also need to be evaluated outside 
of web views and requiring a request object creates friction and this forces 
developers to write fake request objects or write custom wrappers

3. Paid Feature Flag Services: While paid feature flag services offer a lot of 
analytical tools and management dashboards, they are often costly for smaller 
projects, open source applications or teams just starting out. Also integrating 
enterprise level feature flags  services results in increased setup overhead 
and increased dependencies.

A native feature flags framework in Django gives developers a lightweight, 
out-of-the-box solution that works consistently across the entire ecosystem and 
this will also allow teams to keep the cost low while reducing overall dependencies.


Specification
=============

The feature flag framework proposes a unified API design for evaluating flags 
along with a pluggable storage backend. The design decouples flags storage and 
targeting evaluations from request objects which results in consistent checks 
across views, asynchronous coroutines, and background jobs.


Core Public API
---------------

The ``feature`` object provides a method ``is_enabled()`` to check whether a 
flag is active or not.

.. code-block:: python

    from typing import Any


    class FeatureEvaluator:
        """Unified evaluation engine for feature flags."""

        def is_enabled(
            self,
            feature_name: str,
            default: bool = False,
            backend: str = "default",
            context: dict[str, Any] | None = None,
        ) -> bool:
            """
            Check if a feature flag is active.

            Args:
                feature_name: The name of the flag to check.
                default: Fallback boolean returned if the flag does not exist 
                    or an error occurs (defaults to False).
                backend_alias: The storage backend to query from settings 
                    (defaults to "default").
                context: Optional dictionary of attributes to evaluate against 
                    targeting rules.
            """
            ...

When ``feature.is_enabled()`` is called, it evaluates the flag in a particular 
sequence:

* Context Resolution: This merges any implicit context stored in the active 
  ``ContextVar`` with any explicit dictionary passed to ``context``.
* Backend Retrieval: This fetches the flag configuration dictionary from the 
  specified storage backend.
* Kill-Switch: Checks the ``enabled`` boolean.
* Targeting Rules: If conditions exist, the evaluator executes the rules against 
  the resolved context. If no conditions exist, the flag is enabled for all callers.
* Safe Fallback: If the backend raises an exception or the flag definition is 
  missing, it catches the error and returns ``default``.


Basic Usage
-----------

In standard Django views, incoming request metadata and user attributes are 
resolved automatically by the  middleware requiring only the flag name

.. code-block:: python

    from django.shortcuts import render
    from django.features import feature


    def checkout_view(request):
        if feature.is_enabled("NEW_CHECKOUT"):
            return render(request, "new_checkout.html")
        return render(request, "old_checkout.html")

When checks require specific runtime data (like cart value), custom attributes 
can be passed using the ``context`` parameter

.. code-block:: python

    if feature.is_enabled(
        "DISCOUNT_BANNER", context={"cart_total": 5000, "country": "IN"}
    ):
        apply_discount()


Context Management & Asynchronous Safety
----------------------------------------

To decouple flag checks from Django's HTTP ``HttpRequest`` object, runtime 
context is stored using Python's standard ``contextvars.ContextVar``. This 
ensures targeting attributes remain isolated per thread or asynchronous task 
without state bleeding across concurrent requests.

.. code-block:: python

    from contextvars import ContextVar
    from typing import Any

    _FEATURE_CONTEXT: ContextVar[dict[str, Any] | None] = ContextVar(
        "_FEATURE_CONTEXT", default=None
    )


Context Manager for Background Jobs and Testing
-----------------------------------------------

When no HTTP request exists developers can use ``feature.context()`` for user 
identifiers and targeting attributes:

.. code-block:: python

    from django.features import feature

    with feature.context(user_id="user_101", is_staff=True):
        if feature.is_enabled("PROCESS_V2"):
            run_v2_processor()

The context manager applies temporary targeting attributes (such as a user ID 
or role) to any flag evaluations executed inside the ``with`` block, restoring 
the previous context once the block finishes.


Targeting Rules and Deterministic Rollouts
------------------------------------------

The evaluation system supports targeting rules using groups acting as OR operator 
and properties acting as AND operator. A user needs to fall into one of the groups 
and all the properties of that group to get the feature.

.. code-block:: python

    FLAGS = {
        "BETA_DASHBOARD": {
            "enabled": True,
            "conditions": {
                "groups": [
                    # Group 1: Staff members
                    {
                        "properties": [
                            {
                                "key": "is_staff",
                                "operator": "exact",
                                "value": True,
                            }
                        ]
                    },
                    # Group 2: 25% of beta users in India
                    {
                        "properties": [
                            {
                                "key": "country",
                                "operator": "exact",
                                "value": "IN",
                            },
                            {
                                "key": "plan",
                                "operator": "exact",
                                "value": "beta",
                            },
                        ],
                        "rollout_percentage": 25,
                    },
                ]
            },
        }
    }

There are four property operators for attributes: ``exact``, ``is_not``, 
``in`` and ``icontains``.


Percentage Rollouts
~~~~~~~~~~~~~~~~~~~

When ``rollout_percentage`` is set on a group, the user’s id or client cookie is 
combined with flag name and is hashed to get a number between 0 to 100, because 
the calculation is deterministic a user’s assignment is sticky (not random) and 
expanding the rollout from 10% to 25% will not disable the features for users 
who had it initially.


Backends
--------

To support different storages without changing evaluation logic all backends 
must inherit from ``BaseFeatureBackend`` class.

.. code-block:: python

    import abc
    from typing import Any


    class BaseFeatureBackend(abc.ABC):
        """Abstract Base Class for feature flag storage engines."""

        def __init__(self, alias: str = "default", **options: Any) -> None:
            self.alias = alias
            self.options = options

        @abc.abstractmethod
        def get_feature(
            self, feature_name: str, default: Any = False
        ) -> dict[str, Any]:
            """
            Fetch feature configuration by name.
            Must return a dict containing at minimum: {"enabled": bool, "conditions": dict}.
            """
            pass

        @abc.abstractmethod
        def get_all_features(self) -> dict[str, dict[str, Any]]:
            """Fetch all feature definitions for bulk evaluation."""
            pass

The initial implementation ships with two backends:

1. ``SettingsBackend`` - This reads flags from ``settings.py`` useful for basic 
projects or quick testing.
2. ``DummyBackend`` - This is useful for testing purposes.

Backends defined in ``FEATURE_FLAGS`` settings are managed by ``FlagRouter``. 
It lazily imports, initializes, and caches backend instances using a dictionary 
interface, falling back to an in-memory ``DummyBackend`` if no configuration exists.


Request Context Middleware
--------------------------

``FeatureContextMiddleware`` manages runtime context for the duration of each 
HTTP request. For authenticated users, it extracts ``request.user`` and primary 
identifiers directly into the context. For anonymous visitors, it reads or 
creates a persistent device cookie (``ff_client_id``) so sticky percentage 
rollouts remain consistent across sessions, automatically clearing all stored 
context once the response is returned.


Client-Side Flags Endpoint
--------------------------

The framework also provides a built-in JSON view exposed via ``api/flags/``.


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


Reference Implementation
========================

A reference implementation (django-featurevault) is being developed alongside 
this DEP process. This implementation will allow the community to test the 
framework and suggest any necessary changes/features that will be needed before 
the final integration into Django core.   
The reference implementation can be found at https://github.com/prafulgulani/django-featurevault.


Future Iterations
=================

Feature Flags Frameworks offer a vast amount of functionality and developing 
them in phases would be the best way forward. The following features have been 
deemed out of scope for the first phase and can be considered for future iterations. 

* ORM based backend
* Django admin integration
* Multivariate & A/B testing
* Stale flag detection
* Management commands
* Scheduled percentage rollouts
* Flags dependencies and prerequisites
* Metrics for analyzing variants
* Migration tools to import flags from third-party packages


AI Disclosure
=============

Gemini models were used as coding assistants. 


Copyright
=========

This document has been placed in the public domain per the Creative Commons 
CC0 1.0 Universal license (https://creativecommons.org/publicdomain/zero/1.0/deed).