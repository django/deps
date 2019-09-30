=============================
DEP 0005: Improved middleware
=============================

:DEP: 0005
:Author: Carl Meyer
:Implementation Team: Florian Apolloner, Tim Graham, Carl Meyer
:Shepherd: Carl Meyer
:Status: Final
:Type: Feature
:Created: 2016-01-07

.. contents:: Table of Contents
   :depth: 3
   :local:


Abstract
========

The existing Django "middleware" abstraction suffers from a lack of
strict layering and balanced in/out calls to a given middleware. This
DEP proposes an improved abstraction for wrapping the request cycle in
layered pre-view and post-view actions.


Motivation
==========

In theory, and per `the documentation`_, ``process_request`` will be
called for each incoming request, ``process_response`` will be called
for each outgoing response, and ``process_exception`` will be called in
case of an uncaught exception.

This description seems to imply the invariant that if
``process_request`` is called, either ``process_response`` or
``process_exception`` will later be called on that same middleware in
that same request cycle. Django itself has in the past included
middleware (the now-defunct ``TransactionMiddleware``) that implicitly
relied on this invariant.

In fact, due to the short-circuiting and exception-handling behavior of
various middleware methods, this invariant does not hold. It is possible
for a middleware to have its ``process_request`` method called, but then
never see its ``process_response`` or ``process_exception`` called for
that request (e.g. in case of an uncaught exception in a "later"
middleware method).

It is also possible for a middleware to never see its
``process_request`` method called for a given request (because an
earlier middleware's ``process_request`` returned a response), but still
have its ``process_response`` or ``process_exception`` method called on
that response.

This lack of strict in/out layering makes it impossible to safely
implement some types of middleware (such as ``TransactionMiddleware``),
and requires verbose defensive programming: e.g. even if
``process_request`` sets a certain attribute on the request,
``process_response`` on that same middleware can't assume that that
attribute will be present on the request it receives.

This is the primary problem that this DEP intends to solve.

.. _the documentation: https://docs.djangoproject.com/en/1.9/topics/http/middleware/


Acknowledgment
==============

The proposed API in this DEP is modelled on Pyramid's `Tween`_
concept. The author and implementer of this DEP developed a very similar
idea independently at a Django sprint before reading about Tweens.

.. _Tween: http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/hooks.html#registering-tweens


Specification
=============

This DEP introduces a new setting, ``MIDDLEWARE``, which contains an
ordered list of dotted paths to middleware factories.

A middleware factory can be written as a function that looks like this::

    def simple_middleware(get_response):
        # one-time configuration and initialization

        def middleware(request):
            # code to be executed for each request before
            # the view is called; equivalent to process_request

            response = get_response(request)

            # code to be executed for each request/response after
            # the view is called; equivalent to process_response

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

In prose instead of examples: a middleware factory is a callable that
takes a ``get_response`` callable and returns a middleware. A middleware
is a callable that takes a ``request`` and returns a ``response``. (Just
like a view! Turtles all the way down!)

The ``get_response`` callable provided by Django might be the actual
view (if this is the last listed middleware), or it might be the next
middleware in the chain. The current middleware doesn't need to know or
care what exactly it is -- just that it represents "the remainder of
request processing", and that it takes a request and returns a response.

(The above is a slight simplification -- the ``get_response`` callable
for the last middleware in the chain won't be the actual view, it'll be
a wrapper method from the handler which takes care of view middleware,
calling the view with appropriate url args, and template-response
middleware; see below.)

This specification already encompasses the full functionality of
``process_request`` and ``process_response`` (with some differences in
short-circuiting behavior discussed below under "Backwards
Compatibility"). It also allows more powerful idioms that aren't
currently possible, like wrapping the call to ``get_response`` in a
context manager (e.g. ``transaction.atomic``) or in a ``try/finally``
block.


View and template-response middleware
-------------------------------------

This DEP does not propose to change the implementation of view
middleware, exception middleware, or template-response middleware. These
are single-point hooks, not wrappers, and don't suffer from the same
in/out balancing issues. A middleware that wishes to implement one or
both of these hooks should be implemented in the class style, and should
implement ``process_view``, ``process_exception``, and/or
``process_template_response`` methods, exactly as it would today.


Changes in short-circuiting semantics
-------------------------------------

Under the new scheme, middleware will behave more like an "onion", as
described in the documentation. That is, when a middleware
short-circuits the following middleware and the view by returning a
response, that response will only pass through previous middleware in
the list, rather than passing through the ``process_response`` methods
of *all* middleware (including some who never got a crack at
``process_request``), as occurs today.

Similarly, a middleware that modifies the request on the way in and does
pass it on can be guaranteed that it will always see the response on the
way back out.


Exception handling
------------------

Exceptions raised in the view (or in the ``render`` method of a
``TemplateResponse``) are processed through the ``process_exception``
methods of middleware. If any of these return a response, it is passed
back up through the middleware. If not, the exception is converted to a
response (that is, certain special exceptions such as ``Http404``,
``PermissionDenied``, and ``SuspiciousOperation`` are converted to 4xx
HTTP responses, and all other exceptions are converted to ``500 Internal
Server Error``), and that response is passed up through the middleware.

Exceptions raised in a middleware are immediately converted to the
appropriate response type, which is then passed to the next
middleware. Thus, a middleware never needs to be concerned about
handling exceptions when it calls ``get_response()``; it should always
get back a response.


Disabling middleware
--------------------

A middleware can be disabled at setup time, if it's not needed or not
supported under the current settings.

For a class-based middleware, this is achieved the same way as in
current Django: by raising ``MiddlewareNotUsed`` from the ``__init__``
method.

A function middleware factory can either raise ``MiddlewareNotUsed``, or
it can simply return the same ``get_response`` callable it was passed,
instead of a new middleware callable; this has the same effect.


Backwards Compatibility
=======================

"New-style" middleware factories cannot inter-operate
backwards-compatibility in a single mixed list with old-style middlewares,
because the short-circuiting semantics of the two differ. This is why a
new ``MIDDLEWARE`` setting is introduced to contain the new-style
middleware factories. If the ``MIDDLEWARE`` setting is provided (it will
initially be set to ``None`` in the global default settings), new-style
middleware is used. If ``MIDDLEWARE`` is not set, ``MIDDLEWARE_CLASSES``
will behave exactly as it does today. If both are set to non-default
values, the checks framework will flag it as a warning, but
``MIDDLEWARE`` will take priority and ``MIDDLEWARE_CLASSES`` will not be
used.

The implementation of this DEP will include new-style implementations of
all middlewares included in Django; the current implementations will not
be removed. The ``startproject`` template will include a ``MIDDLEWARE``
setting referencing the new-style middleware.


Transition assistance mixin
---------------------------

In order to ease providing the existing built-in middleware in both
new-style and old-style forms, and to ease similar conversions of
third-party middleware, a converter mix-in will be provided, with an
implementation similar to the following::

    class MiddlewareMixin(object):
        def __init__(self, get_response=None):
            self.get_response = get_response
            super(MiddlewareMixin, self).__init__()

        def __call__(self, request):
            response = None
            if hasattr(self, 'process_request'):
                response = self.process_request(request)
            if not response:
                response = self.get_response(request)
            if hasattr(self, 'process_response'):
                # In case we've got an unrendered template response, make sure we
                # delay response handling until it's rendered.
                if hasattr(response, 'render') and callable(response.render):
                    def callback(response):
                        return self.process_response(request, response)
                    response.add_post_render_callback(callback)
                else:
                    response = self.process_response(request, response)
            return response

In most cases, this mixin will be sufficient to convert a middleware
with sufficient backwards-compatibility; the new short-circuiting
semantics will be harmless or even beneficial to the existing
middleware.

In a few unusual cases, a middleware class may need more adjustment to
the new semantics. Some of these cases are documented here (and will
also be documented in the upgrade guide in the Django documentation as
part of the implementation of this PEP):


Seeing all responses
--------------------

An old-style middleware's ``process_response`` method would see (almost)
all outbound responses, even short-circuit responses from the
``process_request`` method of an earlier-listed middleware. This was
often unexpected and caused problems (middleware authors often assumed
that their ``process_request`` and ``process_response`` methods would
always be called as a pair), but it did enable a form of "modify _all_
outgoing responses" that doesn't work under the new system (unless your
middleware is listed first, or any middleware listed before it don't
short-circuit).

In practice, though, this use-case was never complete: a middleware
still wouldn't see any changes to the responses from the
``process_response`` methods of earlier-listed middlewares. Due to this,
and the widespread impression that Django's middleware _already_
implemented onion-style short-circuiting, middleware that desire to see
all outgoing responses generally already instruct their users to place
them first (or at least early) in the middleware list. This advice will
remain both correct and necessary under the new system.

The DEP author conducted a GitHub code search looking for middleware
combinations in existing projects that couldn't work correctly under the
new semantics, and was unable to find any examples. Also, the fact that
Pyramid uses a very similar scheme and has not had problems in this area
is encouraging.


Other differences
-----------------

1. With old-style middleware, ``process_exception`` was applied to
   exceptions raised in middleware ``process_request`` methods. In the
   new system with stricter onion layering, ``process_exception``
   applies only to exceptions raised from the view (or the ``render``
   method of a ``TemplateResponse``).

2. With old-style middleware, an exception raised from a
   ``process_response`` method would skip all remaining
   ``process_response`` methods and be converted into a generic 500
   error (even if it was a special type of exception such as a
   ``Http404``). Now such an exception is immediately converted to the
   appropriate response type, which is passed on to the next middleware
   in line. Middleware are not skipped due to an exception.


Deprecation
-----------

The fallback from a missing ``MIDDLEWARE`` setting to
``MIDDLEWARE_CLASSES`` will be subject to a normal deprecation path. At
the conclusion of that deprecation path, support for the fallback and
the old-style middleware implementations in Django will be removed. The
compatibility mixin will begin its own deprecation path at that
point. (This allows warning-free use of the compatibility mixin
throughout the deprecation path for ``MIDDLEWARE_CLASSES``).


Rationale
=========

The above specification has the advantage that a very similar scheme is
already in use and battle-tested in another widely-used Python web
framework, Pyramid.

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

This approach turned out to have three disadvantages: it is less
backwards-compatible, because it's not compatible with class-based
middleware (when would a class be instantiated?), it doesn't provide any
mechanism for one-time setup or disabling, and it would be slower, since
it requires Django to construct a new chain of closures for every
request, whereas the factory approach allows the closure chain to be
constructed just once and reused for each request.

Forcing middleware to handle exceptions
---------------------------------------

In earlier drafts of this DEP, unhandled exceptions were allowed to
bubble up through middleware layers until caught and handled, as Python
exceptions normally do. Catching exceptions in this way replaced
``process_exception``. This was attractive in its simplicity and
similarity to other Python code, but in practice makes it too difficult
to write useful response-processing middleware, and too difficult to
provide workable backwards-compatibility with old-style middleware.

It's common for middleware to want to modify all outgoing responses in
some way (e.g. add a header). If a middleware gets an exception instead
of a response when it calls ``get_response()``, it has to decide whether
to convert that exception into a response or let it bubble further
up. This results in many different middleware having to duplicate
similar exception-conversion logic. If a middleware wants to modify all
outgoing responses, it has to convert all exceptions to responses, which
shields all later middleware from receiving any view exceptions, making
it hard to usefully implement exception-catching middleware (or at least
imposing strict new ordering requirements on exception-handling vs
response-handling middleware).

Leaving the separate ``process_exception`` hook in place allows all
middleware a chance to handle view exceptions in a separate phase, so
catching exceptions in the response-handling phase becomes less
necessary. Rather than making all middleware implement exception
handling and conversion to a response, we just convert exceptions to
responses before and after every middleware. This makes life much
simpler for middleware authors, allowing them to e.g. ``raise
Http404()`` and know that it will be handled correctly, while also
letting them assume they will get a response (not an exception) from
``get_response()``.


Using a new word
----------------

Django's use of the term ``middleware`` to mean "hooks for munging the
request and/or response in between the web-server interface and the
view" does not appear to be consistent with the primary historical use
of that term in computing (e.g. see `the Wikipedia page`_ on
middleware).

.. _the Wikipedia page: https://en.wikipedia.org/wiki/Middleware

Thus, some have suggested abandoning the term "middleware" with the
deprecation of ``MIDDLEWARE_CLASSES`` and coining a new term (or
borrowing a term like Pyramid's "Tween") for the new system described in
this DEP.

This DEP prefers instead to retain the use of the term "middleware."
However it originated, Django's use of the term appears to already be
widely shared in the web framework world, even beyond Python; it is used
at least by `Flask`_, by `Rack`_, and by `WSGI`_ itself. The scheme
introduced in this DEP is clearly an evolution of Django's existing
middleware, not a brand-new concept, so introducing a brand-new term for
it is likely to cause more confusion than it solves.

.. _Flask: http://werkzeug.pocoo.org/docs/0.11/middlewares/
.. _Rack: https://github.com/rack/rack/wiki/List-of-Middleware
.. _WSGI: http://wsgi.readthedocs.org/en/latest/libraries.html


Pluralization
-------------

Some have suggested naming the new setting ``MIDDLEWARES`` instead of
``MIDDLEWARE``.  There appears to be some debate over the correct
pluralization of "middleware," ranging from those who assert that
"middleware" is already a mass noun (like "furniture") which can never
be used in the singular (and thus we should speak of "a middleware
component," never "a middleware"), to those who prefer "a middleware"
and "middlewares."

This DEP chooses to paint the bikeshed an intermediate color, in which
we may speak of "a middleware" but the plural of "middleware" remains
"middleware."


Reference Implementation
========================

The reference implementation work-in-progress can be found at
https://github.com/django/django/pull/6501/files


Copyright
=========

This document has been placed in the public domain per the Creative
Commons CC0 1.0 Universal license
(http://creativecommons.org/publicdomain/zero/1.0/deed).
