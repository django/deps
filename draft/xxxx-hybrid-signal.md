---
DEP: XXXX Hybrid Signals
Author: Mykhailo Havelia
Implementation Team:
Shepherd:
Status: Draft
Type: Feature
Created: 2025-11-06
Last-Modified: 2025-11-06
---

# DEP XXXX: Hybrid Signal

Table of Contents
- [Abstract](#abstract)
- [Motivation](#motivation)
- [Specification](#specification)
- [Rationale](#rationale)
- [Backwards Compatibility](#backwards-compatibility)
- [Copyright](#copyright)

## Abstract

This DEP proposes the introduction of hybrid signal handlers in Django - signal
receivers that can define different implementations for synchronous (`send`) and
asynchronous (`asend`) dispatch. The goal is to eliminate the need for expensive
`sync_to_async` and `async_to_sync` conversions when signals are triggered in mixed
contexts, while keeping backward compatibility with existing Signal usage.

## Motivation

Currently, Django's signal system doesn't distinguish between synchronous and
asynchronous receivers. A signal can connect either sync or async functions, but
internally Django uses thread-based wrappers (`sync_to_async` or `async_to_sync`) when
dispatching to handlers that don’t match the context type.

Example:

```python
from django.core.signals import request_finished
from django.dispatch import receiver

@receiver(request_finished)
def request_logger(sender, **kwargs):
    print("Request finished")
```

When this signal is triggered using `asend`, Django wraps sync functions using
`sync_to_async`, spawning a thread for each invocation. This adds unnecessary overhead.
A hybrid signal would allow developers and third-party libraries to register both sync
and async versions of a handler explicitly. This way, Django can directly dispatch to
the appropriate function without any cross-context wrapping or thread spawning.

# Specification

A hybrid signal handler can define both sync and async implementations under a single
registration.

Example API:

```python
class HybridSignalHandler:

    def sync_call(self, receiver, **kwargs):
        raise NotImplementedError(
            "send is not supported for this handler"
        )

    async def async_call(self, receiver, **kwargs):
        raise NotImplementedError(
            "asend is not supported for this handler"
        )
```

Usage:

```python
@receiver(request_finished)
class RequestLogger(HybridSignalHandler):
    def sync_call(self, sender, **kwargs):
        print("Request finished (sync)")

    async def async_call(self, sender, **kwargs):
        print("Request finished (async)")
```

## Rationale

Django’s current signal system calls receivers the same way in all contexts.
When an async signal is sent, Django wraps sync receivers with `sync_to_async()`,
which runs them in a thread. This works but adds unnecessary overhead for short signals
and makes async code less efficient. The idea of hybrid signals is simple: allow
developers to define both sync and async versions of the same handler. Then Django
can call the right one directly, without using wrappers or threads.

This design:

- avoids extra thread spawning and context switching
- keeps signals simple and backward compatible
- and gives developers clear control over how their handlers run

Similar patterns already exist in other frameworks, for example in `Strawberry GraphQL`,
where extensions can define both `resolve()` and `resolve_async()`.


## Backwards Compatibility

This proposal is fully backward compatible:

- Existing Signal and receiver decorators continue to work as is.
- Libraries can safely migrate incrementally.

Potential risks:

- None for existing code.
- Minimal risk if developers misdefine hybrid handlers (guarded by `NotImplementedError`).

## Copyright

This document has been placed in the public domain per the Creative
Commons CC0 1.0 Universal license
(<http://creativecommons.org/publicdomain/zero/1.0/deed>).

(All DEPs must include this exact copyright statement.)
