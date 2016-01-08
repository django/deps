================================
DEP 0005: Re-thinking middleware
================================

:DEP: 0005
:Author: Carl Meyer
:Implementation Team: Florian Apolloner
:Shepherd: Carl Meyer
:Status: Draft
:Type: Feature
:Created: 2016-01-07
:Last-Modified: 2016-01-07

.. contents:: Table of Contents
   :depth: 3
   :local:


Abstract
========

The existing Django "middleware" abstraction suffers from an absence of strict
layering and balanced in/out calls to a given middleware. This DEP proposes an
improved abstraction for wrapping the request cycle in strictly layered
pre-view and post-view actions.


Motivation
==========

In theory, and per `the documentation`_, ``process_request`` will be called for
each incoming request, ``process_response`` will be called for each outgoing
response, and ``process_exception`` will be called in case of an uncaught
exception.

This description seems to imply the invariant that if ``process_request`` is
called, either ``process_response`` or ``process_exception`` will later be
called on that same middleware in that same request cycle. Django itself has in
the past included middleware (the now-defunct ``TransactionMiddleware``) that
implicitly relied on this invariant.

In fact, due to the short-circuiting and exception-handling behavior of various
middleware methods, this invariant does not hold. It is possible for a
middleware to have its ``process_request`` method called, but then never see
its ``process_response`` or ``process_exception`` called for that request
(e.g. in case of an uncaught exception in a "later" middleware method).

It is also possible for a middleware to never see its ``process_request``
method called for a given request (because an earlier middleware's
``process_request`` returned a response), but still have its
``process_response`` or ``process_exception`` method called on that response.

This lack of strict in/out layering makes it impossible to safely implement
some types of middleware (such as ``TransactionMiddleware``), and requires
verbose defensive programming: e.g. even if ``process_request`` sets a certain
attribute on the request, ``process_response`` on that same middleware can't
assume that that attribute will be present on the request it receives.

This is the primary problem that this DEP intends to solve.

.. _the documentation: https://docs.djangoproject.com/en/stable/topics/http/middleware/


Acknowledgment
==============

The proposed API in this DEP is modelled on Pyramid's `Tween`_ concept (the
author and implementor of this DEP developed a very similar idea independently
at a Django sprint before reading about Tweens).

.. _Tween: http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/hooks.html#registering-tweens

Specification
=============

This DEP introduces a new setting, ``MIDDLEWARE``, which contains an ordered
list of dotted paths to middleware factories.

A middleware factory can be written as a function that looks like this::

    def simple_middleware(get_response):
        # one-time configuration and initialization

        def middleware(request):
            # code to be executed for each request before
            # the view is called

            response = get_response(request)

            # code to be executed for each request/response after
            # the view is called

            return response

        return middleware

Or it can be written as a class with a ``__call__`` method, like this::

    class SimpleMiddleware(object):
        def __init__(self, get_response):
            self.get_response = get_response

            # one-time configuration and initialization

        def __call__(self, request):
            # code to be executed for each request before
            # the view is called

            response = self.get_response(request)

            # code to be executed for each request/response after
            # the view is called

            return response

In prose instead of examples: a middleware factory is a callable that takes a
``get_response`` callable and returns a middleware. A middleware is a callable
that takes a ``request`` and returns a ``response``. (Just like a view! Turtles
all the way down!)

The ``get_response`` callable provided by Django might be the actual view (if
this is the last listed middleware), or it might be the next middleware in the
chain. The current middleware doesn't need to know or care what exactly it is
-- just that it represents "upstream", and that it also takes a request and
returns a response.

(The above is a slight simplification -- the ``get_response`` callable for the
last middleware in the chain won't be the actual view, it'll be a wrapper
method from the handler which takes care of view middleware, calling the view
with appropriate url args, and template-response middleware; see below.)


Disabling middleware
--------------------

A middleware can be disabled at setup time, if it's not needed or not supported
under the current settings.

For a class-based middleware, this is achieved the same way as in current
Django: by raising ``MiddlewareNotUsed`` from the ``__init__`` method.

A function middleware factory can either raise ``MiddlewareNotUsed``, or can
simply return ``None`` instead of a middleware callable.


View and template-response middleware
-------------------------------------

The above examples already encompass the full functionality of
``process_request`` (this is the code that goes before the call to
``get_response``), ``process_response`` (the code that goes after), and
``process_exception`` (just place the call to ``get_response`` within a
``try/except`` block). It also allows more powerful idioms, like wrapping the
call to ``get_response`` in a context manager (e.g. ``transaction.atomic``).

This DEP does not propose to change the implementation of view middleware or
template-response middleware (since these are really single-point hooks, not
wrappers, and don't suffer from the same in/out balancing issue). A middleware
that wishes to implement one or both of these hooks should be implemented in
the class style, and should implement ``process_view`` and/or
``process_template_response`` methods, exactly as it would today.


Changes in short-circuiting semantics
-------------------------------------

Under the new scheme, middleware really will behave more like an "onion", as
described in the documentation. That is, when a middleware short-circuits the
upstream middleware and view by returning a response, that response will only
pass through previous middleware in the list, rather than passing through the
``process_response`` methods of *all* middleware (including some who never got
a crack at ``process_request``), as occurs today.

Similarly, a middleware that modifies the request on the way in and does pass
it on upstream can be guaranteed that it will always see the response on the
way back out. (If it also wants to see any uncaught exception on the way out,
it can just wrap its call to ``get_response`` in a ``try/except``).


Backwards Compatibility
=======================

"New-style" middleware factories cannot inter-operate backwards-compatibly in a
single mixed list with old-style middlewares, because it is not possible to
maintain both the "in/out balanced" invariant of the new and the existing
short-circuiting behaviors of the old. This is why a new ``MIDDLEWARE`` setting
is introduced to contain the new-style middleware factories. If the
``MIDDLEWARE`` setting is provided (it will initially be set to ``None`` in the
global default settings), the old ``MIDDLEWARE_CLASSES`` setting will be
ignored. If ``MIDDLEWARE`` is not set, ``MIDDLEWARE_CLASSES`` will behave
exactly as it does today.

The implementation of this DEP will include new-style implementations of all
middlewares included in Django; the current implementations will not be
removed. The ``startproject`` template will include a ``MIDDLEWARE`` setting
referencing the new-style middleware.

Transition assistance mixin
---------------------------

In order to ease providing the existing built-in middleware in both new-style
and old-style forms, and to ease similar conversions of third-party middleware,
a converter mix-in will be provided, with an implementation similar to the
following::

    class MiddlewareConversionMixin(object):
        def __init__(self, get_response):
            self.get_response = get_response
            super(MiddlewareMixin, self).__init__()

        def __call__(self, request):
            response = None
            if hasattr(self, 'process_request'):
                response = self.process_request(request)
            if not response:
                try:
                    response = self.get_response(request)
                except Exception as e:
                    if hasattr(self, 'process_exception'):
                        return self.process_exception(request, e)
                    else:
                        raise
            if hasattr(self, 'process_response'):
                response = self.process_response(request, response)
            return response

In most cases, this mixin will be sufficient to convert a middleware with
sufficient backwards-compatibility; the new short-circuiting semantics will be
harmless or even beneficial to the existing middleware. In a few unusual cases,
a middleware class may need more invasive changes to adjust to the new semantics.


Deprecation
-----------

The fallback from a missing ``MIDDLEWARE`` setting to ``MIDDLEWARE_CLASSES``
will be subject to a normal deprecation path. At the conclusion of that
deprecation path, support for the fallback, the old-style middleware
implementations in Django, and the conversion mixin, will be removed.


Rationale
=========

The above specification has the advantage that a very similar scheme is already
in use and battle-tested in another widely-used Python web framework, Pyramid.

Alternatives considered and rejected:

Simple functions
----------------

Earlier drafts of this proposal suggested that a middleware could be
implemented as a simple function that took both ``request`` and
``get_response`` directly, rather than as a factory::

    def simple_middleware(request, get_response):
        # request-munging
        response = get_response(request)
        # response-munging
        return response

This approach turned out to have two disadvantages: it was less
backwards-compatible, because it's not compatible with class-based middleware
(when would a class be instantiated?), and it would be slower, since it
requires Django to construct a new chain of closures for every request, whereas
the factory approach allows the closure chain to be constructed just once and
reused for each request.


Using generators
----------------

It would be possible to eliminate the need to pass in a ``get_response``
callable by turning middleware into generators which would ``yield`` the
request, and then Django would call ``.send(response)`` on the generator object
to pass back in the response. In that case a middleware body might look like this::

    def simple_middleware(request):
        # request-munging
        response = yield request
        # response-munging
        return response

This is clever; probably too clever. In the end it doesn't provide any useful
benefits over the approach proposed above and takes advantage of Python
features that are unfamiliar to many developers (generators that receive
values).


Reference Implementation
========================

The reference implementation work-in-progress (which as of this writing doesn't
yet implement the proposal described here, but rather an earlier iteration) can
be found at https://github.com/django/django/pull/5591/files


Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).
