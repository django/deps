======================
DEP XXXX: Unasyncify Codegen
======================

:DEP: XXXX
:Author: Raphael Gaschignard
:Implementation Team: TODO (Raphael Gaschignard + others?)
:Shepherd: TODO
:Status: Draft
:Type: Feature
:Created: 2024-10-26
:Last-Modified: 2014-10-26

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

This DEP proposes to add code generation tooling (Unasyncify codegen) to Django as a way to implement DEP 0009 without duplicating code.

Unasyncify codegen takes an async function and transforms it into a synchronous variant. This involves "eraising" ``await`` s, making sure to call sync versions of async functions found in the function body, and other syntactic-level transformations as needed.

The code generation lets us have one canonical implmentation (the async one) for APIs using this code generation, while still being able to easily add code that is only used in the async or sync variants.

The codegen would be run by Django developers and checked into the codebase. This would allow for complete visibility into what the tool does, and ensure that users of Django are not presented with obfuscated code when looking at internal calls.

Motivation
==========

In order to implement DEP 0009, we want to implement asynchronous APIs for various synchronous APIs. Generally speaking, the color problem means that implementing async APIs and sync APIs involve writing extremely similar-looking code twice.

Code duplication is error-prone, because one has to be very confident that there is no implementation drift between each variant. Having a single canonical version would be helpful!

But if the sync version of ORM APIs are the canonical ones, we cannot take full advantage of what ``async`` offers. Inversely, if the async version of ORM APIs were considered canonical, then sync ORM APIs would likely have to pay a serious performance cost (through something like ``async_to_sync``).

Psycopg is another project facing a similar difficulty for implementing both synchronous and asynchronous APIs without having either side pay a penalty for the other existing.
`Their strategy <https://www.psycopg.org/articles/2024/09/23/async-to-sync/>`_ was to treat the asynchronous version as canonical, and to generate the code for the synchronous version from the async source.
There is no runtime cost for the sync code relative to the async code, but there is only one implementation that needs to be maintained.

Progress on DEP 0009 has meant that async variants of APIs have a certain naming convention. This naming convention, combined with the straightforward nature of async-to-sync generation, makes Django's code base amenable to a purely syntactic transformation.

Specification
=============
A new module is added, ``django.utils.codegen``. Inside it are several decorators:

* ``generate_unasynced(*, async_unsafe=False)``, a decorator which marks functions to be transformed
* ``from_codegen``, a decorator that marks functions that were generated through unasync codegen.

This module also includes the following:

* ``ASYNC_TRUTH_MARKER``
  This is ``True``. But during codegen this gets replaced with ``False``. This allows us to easily mix async and sync "branches" within the same implementation for the times we need it.
  This is a bit similar to ``typing.TYPE_CHECKING``.

A new script is added, ``scripts/run_codegen.sh``, that scans Django's source tree for functions that need unasync codegen applied.

A function annotated with ``@generate_unasynced()`` is marked to have the unasync codegen applied to it.

* The annotated function must be an ``async def``'d function
* Its name must follow Django's "async variant" naming convention, either beginning with ``a`` or, in the case of internal functions, ``_a``

Unasync codegen will add a new function to the same block, above the existing function implementation.


The generated function has the following changes:

* This function is named as the "sync variant", removing the ``a``
  ``aconnect`` becomes ``connect``
  ``_ainternal_method`` becomes ``_internal_method``
* The ``@generate_unasynced`` decorator is removed
* A ``@from_codegen`` decorator is added. This both indicates to the reader of code that this is from code generation, and lets code generation be idempotent
* The generated function is synchronous (``def foo``)
* Certain names are replaced in the body, whether they are used as identifiers or attributes.
  Currently the mapping is as follows:

  * ``aconnection`` -> ``connection``
    (This allows for simple remapping of ``self.aconnection`` to ``self.connection``)
  * ``ASYNC_TRUTH_MARKER`` -> ``False``
    (``ASYNC_TRUTH_MARKER is True``, but we can use this marker to have code know if it is in the async or sync variant of a function)
  * Other names might be added based on needs we discover working on this.
* ``if ASYNC_TRUTH_MARKER`` blocks are flattened in the sync variant
  Concreteley, this means that the following::

    if ASYNC_TRUTH_MARKER:
        do_thing_a()
    else:
        do_thing_b()

  Gets flattened to just::

    do_thing_b()


* ``await``'ed  expressions are replaced with non-await versions:

  * Within an ``await`` 'ed expression, function calls are examined to see if their name starts with `a`. If so, we replace this with function calls without the `a`

    Concretely, this means that ``await objects.aget(foo=bar)`` will get transformed to ``objects.get(foo=bar)``.
    This transformation only happens inside of expressions within an ``await``, so something like ``my_dict.add(foo=bar)`` *will not* be transformed.

    This transformation also only looks at function calls, and not attributes. This is why we also have a separate transformation to handle rewriting ``aconnection`` to ``connection``.

    This does mean that ``await objects.aget(foo=obj.afunc())`` would get transformed to ``objects.get(foo=obj.func())`` (note the change from ``afunc`` to ``func``).
    One can avoid this by extracting the call::

      result = obj.afunc()
      await objects.get(foo=result)

    Or one can also use something like ``getattr``::

      await objects.get(foo=getattr(obj, 'afunc')())

    This sort of workaround is sufficient to avoid having to have any more complicated "opt out of function renaming" issues. See the Rationale section for a note on this function renaming choice.

* ``async for`` loops are replaced with ``for`` loops
* ``async with`` blocks are replaced with ``with`` blocks
* If, inside the ``generate_unasynced`` decorator, we have specified ``async_unsafe=True``, then the generated function will have ``@async_unsafe`` applied to it as well.


What follows is a concrete example of what the transformation generates.

Given the following::

    @generate_unasynced(async_unsafe=True)
    async def aconnect(self):
        """Connect to the database. Assume that the connection is closed."""
        # Check for invalid configurations.
        self._pre_connect()
        if ASYNC_TRUTH_MARKER:
            # Establish the connection
            conn_params = self.get_connection_params(for_async=True)
        else:
            # Establish the connection
            conn_params = self.get_connection_params()
        self.aconnection = await self.aget_new_connection(conn_params)
        await self.aset_autocommit(self.settings_dict["AUTOCOMMIT"])
        await self.ainit_connection_state()
        connection_created.send(sender=self.__class__, connection=self)

        self.run_on_commit = []

The following is added *above the ``aconnect``* definition::

    @from_codegen
    @async_unsafe
    def connect(self):
        """Connect to the database. Assume that the connection is closed."""
        # Check for invalid configurations.
        self._pre_connect()
        # Establish the connection
        conn_params = self.get_connection_params()
        self.connection = self.get_new_connection(conn_params)
        self.set_autocommit(self.settings_dict["AUTOCOMMIT"])
        self.init_connection_state()
        connection_created.send(sender=self.__class__, connection=self)

        self.run_on_commit = []


By running the ``scripts/run_codegen.sh`` script, Django's source tree is scanned for functions with the ``generate_unasync`` decorator, and will rewrite files with that decorator applied according to the above rules.

Developer Flow Changes
======================

With this change, async functions annotated with ``@generate_unasyncify`` will be considered the "canonical" versions, wheras generally (at the time of this writing) the synchronous version has been the canonical version.

Because of this, developers will need to make sure they make changes to the asynchronous versions of functions annotated with ``@generate_unasyncify``, and not make manual changes to functions with ``@from_codegen`` applied.

An added step in CI will make sure that unasyncify codegen is applied. This also will help capture whether manual changes to the synchronous versions are unintentionally committed.

Developers working on annotated code will need to run ``scripts/run_codegen.sh`` and commit changes from this codegen. This has the added benefit of reviewing the result of the codegen, and supervising that the transformation matches what we want.



Rationale
=========

Factoring out everything but the code flow in a way to minimize code duplication, while doable in a case-by-case way, ultimately means that code would need to be concerned more with async/sync compatibility than with readability as a whole. Factoring out small fragments of code for the sake of async/sync compatibility will make it harder to spot other issues. And even beyond that, the simple act of trying to keep function signatures in sync could lead to issues.

Run-time trickery to try and have a single implementation for both variants bring up the performance question. Load-time transformation of a single implementation would be costly.

Code generation is, fundamentally, legible. Though developers aren't directly writing the generated functions, the results will show up in code review, will be diffed against existing implementations, and won't be obfuscated when looked at by users of Django.

For the specific choice of function call renaming by looking at the name: Using ``a``-prefixed names as a proxy for "async variants of sync APIs" works unreasonably well based on Django's code base. It prevents having to generate a whole list of functions and lets the code transformation remain purely syntactic.

But importantly, this transformation (that happens *only in ``await`` expressions* and *only on names that are being called*) is legible. One can see the transformation happen (because it is checked in), and if someone identifies this issue, they can apply a workaround. Unlike any runtime routing, issues downstream of this rewrite will be visible immediately.

This codegen is aimed at supporting Django's efforts at maintaining these APIs, so we can rely on Django's specific naming conventions. It is not aimed at supporting other project's efforts at maintaining async and sync variants.

Backwards Compatibility
=======================

Because the annotation and transformations associated to it are opt-in, there are no backwards compatibility concerns. Discussion of handling backwards compatibility related to implementing DEP 0009 are out of scope, in the author's opinion, though very important.

Reference Implementation
========================

`This pull request <https://github.com/fcurella/django/pull/4>`_ includes an implementaiton of code generation to move from having sync and async implementations of functions handling database cursors, to a single async implementation (with the sync implementation being derived through code generation).

This code generation uses `libCST <https://libcst.readthedocs.io/en/latest/index.html>`_, which allows for code transformations that in particular preserve comments and whitespace layouts.
This implementation was done in a couple of hours, almost entirely thanks to the existence of ``libCST``. The simplicity of the implementation should be an indicator of the feasibility.


.. rubric:: Footnotes
.. [#color-problem] shortly: I can call sync functions from async functions but not async functions from sync ones. Idea originating from `This blog post <https://journal.stuffwithstuff.com/2015/02/01/what-color-is-your-function/>`_.
