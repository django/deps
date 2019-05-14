==============================
DEP 0009: Async-capable Django
==============================

:DEP: 0009
:Author: Andrew Godwin
:Implementation Team: Andrew Godwin (initially; others later)
:Shepherd: Andrew Godwin
:Status: Draft
:Type: Feature
:Created: 2019-05-06
:Last-Modified: 2019-05-06

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

This DEP proposes to add support for asynchronous Python into Django, while
retaining synchronous Python support as well in a backwards-compatible fashion.


Foreword
========

Asynchronous Python has been in development for many years, and in the Django
ecosystem we have experimented with it via the Channels_ projects,
positioned primarily around WebSocket support.

As the space has matured, it has become apparent that while there is no
immediate need to extend Django to handle non-HTTP protocols like WebSockets,
there are a large set of advantages to supporting async code within Django's
traditional model-view-template structure.

The advantages are explored more in *Motivation* below, but the overall
conclusion I reach is that we have so much to gain from making
Django async-capable that it is worth the large amount of work it will take. I
also believe, crucially, that we can undertake this change in an iterative,
community-driven way that does not rely solely on one or two long-time
contributors burning themselves out.

While this is labeled as a "Feature" DEP, those reasons mean that it is also
partially a Process DEP. The scope of the changes proposed below are incredibly
large, and to run them as a traditional single-feature process would
likely fail badly.

Of course, throughout this entire document it is important to remember the
Django philosophy of always keeping things safe and backwards-compatible. The
plan is not to remove synchronous Django - the plan is to keep that around,
working as it does now, with asynchronous code being an option for those that
feel they need the extra performance or flexibility.

Is this a mammoth task? Of course it is. But I also feel it has the possibility
to substantially reshape the future of Django - we have the opportunity to take
both a trusted framework and an incredible community and inject a whole new set
of options that were not previously possible before.

The Web has changed, and Django must change with it - but by bringing our core
ideals of being approachable, safe by default, and flexible as projects grow and
their needs change. In a world of hosted datastores, service-oriented
architecture, and backend as the bastion of complex business logic,
the native ability to run things concurrently is key.

This DEP outlines the plan I think will get us there. It's a vision I very
much believe in, and which I will work to help us achieve to the best of my
ability and time. At the same time, close examination and skepticism is
warranted; I ask for your constructive criticism as well as your trust.
Django is built on the strength of its community of people and the apps they
build, and if we must set the path for the future, we must all do it together.

.. _Channels: http://channels.readthedocs.io


High-Level Summary
==================

We are going to take Django and add on support for asynchronous views,
middleware, ORM, and other key pieces.

This will be done by running synchronous code in threads at first, but slowly
replacing that with natively-asynchronous code. Synchronous APIs will continue
to exist and be fully supported, with some eventually turning into synchronous
wrappers of natively async code.

ASGI mode will run Django as a native async application. WSGI mode will run a
single event loop around each Django call to make the async handling layer
compatible with a synchronous server.

Threading around the ORM is tricky, and requires a new concept of connection
contexts and sticky threads for running synchronous ORM code in.

A lot of Django will continue to be synchronous, and our goal will be to support
users writing views in both styles, letting them choose the best style for the
view they are working on.

Some features, like templating and cache backends, will need their own
separate DEPs and research to be fully async. This DEP mostly focuses on the
HTTP-middleware-view flow and the ORM.

There will be full backwards compatibility. A standard Django 2.2 project
should load and run in async Django (be that 3.0 or 3.1) with no changes.

The project is designed to be done in small, iterative parts and landed to
Django's ``master`` branch progressively to avoid the problems of a long-running
fork, and to allow us to change course as we discover issues.

This is a good opportunity to bring on new contributors. We should fund the
project to make it happen faster. Funding will be at a scale we are not used to.


Specification
=============

The overall goal is to have every single part of Django that could be blocking -
that is, which is not just simple CPU-bound computation - be async-native
(run in an asynchronous event loop without blocking).

This includes features like:

* Middleware
* Views
* The ORM
* Templating
* Testing
* Caching
* Form validation
* Emails

However, it doesn't include things like internationalization - which would have
no performance benefit as it is CPU-bound and runs quickly - or migrations,
which are single-threaded as they are run in a management command.

Every single feature that is converted to be async internally will also present
a synchronous interface that is backwards-compatible with the API as it stands
today (in 2.2), for the foreseeable future - we might change the sync APIs over
time to make them line up better, but sync APIs are not going away.

An overview of how this is achieved technically is below, followed by specific
implementation details for specific areas. It is not exhaustive to all Django
features, but if we hit this initial target then we will have enabled nearly
all use-cases.

The final part of this section, *Sequencing*, also looks at how these changes
can be done incrementally and by multiple teams in parallel, which is important
to complete these changes with volunteer help in a reasonable timeframe.

Technical Overview
------------------

The principle that allows us to achieve both sync and async implementations in
parallel is the ability to run one style inside of the other.

Each feature will go through three stages of implementation:

* Sync-only (where it is today)
* Sync-native, with an async wrapper
* Async-native, with a sync wrapper

Async Wrapper
~~~~~~~~~~~~~

Initially, the existing synchronous code will be wrapped in an asynchronous
interface that runs the synchronous code inside a threadpool. This will allow us
to design and ship the async interface relatively quickly, without having to
re-implement the entire feature using native async code underneath.

The tooling for this is already available in asgiref_ as the ``sync_to_async``
function, and handles things like exception handling and threadlocals (more
on that below).

Running code in threads is likely not going to increase performance - the
overhead added will probably decrease it very slightly in the
case where you're just running normal, linear code - but it will enable
developers to start running things concurrently and get used to designing
code around these new possibilities.

In addition, there are several parts of Django that are sensitive to being run
in the *same* thread when they are re-entered; for example, database transaction
handling. If we were to wrap an ``atomic()`` around some code that then went
and called the ORM in a series of random threads drawn from a pool, the
transaction would not effect any of them reliably as it is tied to the
connection inside the thread that the transaction was started in.

These situations call for a "sticky thread", where an asynchronous context calls
all synchronous code in the same thread serially, rather than spinning it off
to run in a pool of threads, keeping the apparent behavior of the ORM and other
thread-sensitive parts correct. All parts of Django that we suspect need this
requirement, including the entire ORM, will use a version of ``sync_to_async``
that respects this, so we are safe by default. Users will be able to selectively
disable it to run queries concurrently - see "The ORM" below for more details.

Async Native
~~~~~~~~~~~~

The next step is then to take the feature to be natively written in an async
fashion, and then presenting a synchronous interface via a wrapper that runs
the asynchronous code in a one-off event loop. This is already available in
asgiref_ as the ``async_to_sync`` function.

Not all features will necessarily need to get to the third stage, and be
natively async, quickly. We can focus our efforts on the parts that we can do
well and that have third-party library support, while helping the rest of the
Python ecosystem on things that we need more groundwork on to make natively
asynchronous.

This general overview works on nearly all features on Django that need to be
async, with the exceptions mostly being places where the Python language itself
does not provide async equivalents to features we already use. The outcome there
will either be a change to how Django presents its API in async mode, or working
with the Python core language contributors to help develop Python's async
capabilities.

.. _asgiref: http://github.com/django/asgiref/

Threadlocals
------------

One base implementation detail of Django that needs calling out separately from
most of the feature-based notes below are threadlocals. As their name suggests,
threadlocals only work within threads, and while Django *does* keep the
``HttpRequest`` object out of a threadlocal, we put several other things into
them - like database connections, or the current translation locale.

These threadlocal uses can be separated out into two variants:

* "Context locals", where the value is needed inside of some stack-based context
  like a request. This is where the translation locale falls.

* "True threadlocals", where the code being protected is actually unsafe to
  call from another thread. This is where database connections fall.

It may seem at first glance that "context locals" could be solved by the new
contextvars_ feature in Python, but Django 3.0 will still have to support
Python 3.6, while that feature appears in 3.7. In addition, ``contextvars`` are
specifically designed to cut out of their context when a switch happens, like
into a new thread, while we need to persist those values across those boundaries
to allow the ``sync_to_async`` and ``async_to_sync`` functions to be drop-in
wrappers.

This has already been addressed with the asgiref_ implementation of ``Local``,
which is a coroutine- and thread-compatible local that provides the seamless
experience that existing Django code is built on. It currently does not use
``contextvars``, but we may switch it to work with the 3.6 backport package
after some further testing.

True threadlocals, on the other hand, can continue to just work purely based
on the current thread. We must be more careful, though, to prevent cross-thread
leakage of these objects; when a view no longer runs in the same thread, but
instead spawns a thread per ORM call (while the ORM is in the "sync native,
async wrapper" stage), some things that were previously possible with the
``connection`` object will no longer be possible.

These will require individual attention, and the banning of some previously
possible operations if you are in async mode; the cases we know about are
covered below in the specific sections.

.. _contextvars: https://docs.python.org/3/library/contextvars.html


Simultaneous Sync & Async Interfaces
------------------------------------

One of the big issues we will face trying to port Django over is that Python
does not make it possible to provide both a synchronous and an asynchronous
version of a function/method with the same name.

That means you can't nicely convert an API, for example the cache API, so that
it works like this::

    # Sync version
    value = cache.get("foo")
    # Async version
    value = await cache.get("bar")

This is an unfortunate restriction of the way async is implemented in Python,
and there is no apparent way around it. When something is called, you don't know
if you're being called to then be awaited or not, so there's no possibility of
being able to determine what version to return.

.. note::

    This is because Python implements async callables as "sync callables that
    return a coroutine", rather than "run an ``__acall__`` method on the
    object". Async context managers and iterators don't have this issue, as
    they have separate ``__aiter__`` and ``__aenter__`` methods.

Given this, we must namespace the sync and async variants away from each other
so they don't conflict. We could do this with a ``sync=True`` keyword argument,
but this leads to messy function/method bodies and doesn't allow the use of
``async def``, as well as being rather easy to slip up on and forget the
keyword argument. Accidentally calling a synchronous method when you meant to
call it asynchronously is silently dangerous.

The suggested solution for the large majority of the Django codebase is to
provide an "async" suffixed variant of functions/methods - e.g.
``cache.get_async`` to supplement ``cache.get``. While this is an
ugly solution, it's also the easiest to catch mistakes in when
code reviewing (you must match ``await`` with an ``_async`` method).


Views & HTTP Handling
---------------------

Views are maybe the keystone of this conversion and where we expect most users
to make the choice between async and sync code.

Django will support two kinds of views:

* Synchronous views, defined as they are now by a synchronous function or class
  with a synchronous ``__call__``

* Asynchronous views, defined by an asynchronous function (one that returns a
  coroutine) or a class with an asynchronous ``__call__``.

This will be handled by the ``BaseHandler``, which will inspect the view object
it ends up with from the URL resolver system and then call it in the appropriate
fashion. The base handler will need to be the first part of Django that is
natively asynchronous, and we will need to modify the WSGI handler to call it
in its own event loop using ``async_to_sync``.

Asynchronous views will continue to be wrapped in an ``atomic()`` block if
``ATOMIC_REQUESTS`` is ``True``. While this reduces performance gains, as it
locks all ORM queries to a single thread (see "The ORM" below), it is what our
users will expect and much safer. If they want to run queries concurrently, they
will have to explicitly opt out of having the transaction around the view using
the existing ``non_atomic_requests`` mechanism, though we will need to improve
the documentation around it.

The existing ``StreamingHttpResponse`` class will be modified to be able to take
either a synchronous or an asynchronous iterator, and then have its internal
implementation always be async-native. This will also be true for
``FileResponse``. As this is a potential point of backwards-incompatibility for
third-party code that is directly touching response objects, we will still
need to provide a synchronous ``__iter__`` for the transition period.

WSGI will still continue to be supported by Django into the indefinite future,
but the WSGI handler will transition to running the natively-async middleware
and view handling layer inside of its own, one-off event loop. This will
probably have a small performance penalty, but in initial experiments it has
not had too much impact.

All async HTTP features will work inside WSGI, including long-polling and
slow responses, but they will be as inefficient as today, taking up a server
thread/process per connection. ASGI servers will be the only ones able to
support many concurrent requests efficiently, as well as terminate non-HTTP
protocols such as WebSocket for use by extensions like Channels.


Middleware
----------

While the previous section discusses most of the request/response path,
middleware needs its own section due to the complexity implied by Django's
most recent middleware design.

Django middleware is currently constructed as a stack, where each middleware is
fed the ``get_response`` callable of the middleware below it (or the view for
the bottom middleware in the stack). However, we need to be able to support a
mixture of synchronous and asynchronous middleware, for backwards compatibility
if nothing else, and these two types will not be able to call each other
natively.

Thus, in order to allow for middleware to work, we will have to instead
initialize each middleware with a placeholder get_response that instead feeds
control back out into the handler, and handles both the passing of data between
the middleware and the view as well as exception propagation. In some ways, this
will end up looking more like Django 1.0 era middleware again from an internal
perspective, though of course the user-facing API will remain the same.

We have the option of deprecating synchronous middleware, but I recommend
against doing this in the short term. If and when we got to the end of the
deprecation cycle for that, we could then return the middleware implementation
to a pure recursive stack model as it is today.


The ORM
-------

The ORM is the largest part of Django by code size, and also the most complex to
convert to being asynchronous.

A lot of this stems from the fact that the underlying database drivers are
synchronous by design, and progress will be slow towards a set of mature,
standardized, async-capable database drivers. Instead, we must initially design
around a future where database drivers are synchronous, and set the groundwork
for contributors to iterate on and develop asynchronous drivers.

The problems with the ORM fall into two main categories - threads, and implicit
blocking.

Threads
~~~~~~~

The main issue with the ORM is that Django is designed around a single, global
``connections`` object, which magically gives you the appropriate connection for
your current thread.

In an asynchronous world - where all coroutines run on the same underlying
Python thread - this goes beyond being annoying to being outright dangerous.
Without any extra safety, a user calling the ORM the way they do today would
risk cross-thread pollution of the connection objects.

Fortunately, connection objects are at least portable across threads, even if
they cannot be called from two of them simultaneously. Django already handles
most thread-safety for database drivers in the ORM code, and so we have a place
to modify its behavior to work correctly.

We will change the ``connections`` object to be something that understands both
coroutines and threads - reusing some code from ``asgiref.local`` but adding in
additional logic. Connections will be shared across async and sync code that
calls each other - with context being passed down through ``sync_to_async`` and
``async_to_sync`` - and synchronous code will be forced to run serially in
a single "sticky thread" so that they cannot run simultaneously and break
thread-safety.

What this implies is that, overall, we need a context-manager like solution to
opening and closing the need for a database connection, much like ``atomic()``.
This will enable us to enforce serial calling and sticky threads within that
context, and allow users to make several contexts if they wish to open
multiple connections. It also gives us a potential route out of the magical
``connections`` global if we want to develop it further.

Right now, Django has no lifecycle management around connections that doesn't
depend on the signals from the handler class, and so we will use these to create
and clean up these "connection contexts". Documentation will also be updated to
make it clearer how to do correct connection handling outside of the
request/response cycle; even in the current code, many users are unaware that
any long-running management command has to periodically call
``close_old_connections`` to work correctly.

Backwards compatibility means we must let users access ``connections`` from any
random code whenever they like, but we will only allow this for synchronous
code; we will enforce that code is wrapped in a "connection context" if it is
asynchronous, from day one.

It may seem like this would be a nice thing to add to ``transaction.atomic()``,
and then pair it up with a new ``transaction.autocommit()`` and require users
to run all code within one of them, but that would lead to confusion about what
happens when you nest them inside each other.

Instead, I propose that we create a ``db.new_connections()`` context manager
that enables this behavior, and have it create a new connection whenever
it is called, allowing arbitrary nesting of ``atomic()`` within it.

Whenever a ``new_connections()`` block is entered, Django sets a new context
with new database connections. Any transactions that were running outside the
block continue; any ORM calls inside the block operate on a new database
connection and will see the database from that perspective. If the database
has transaction islation enabled, as most do by default, this means that the
new connections inside the block may not see changes made by any uncommitted
transactions outside it.

On top of this, the connections inside this ``new_connections`` block can
themselves use ``atomic()`` to start additional transactions on those new
connections. Any nesting of these two context managers will be allowed, but
every time ``new_connections`` is used the transactions that were already open
are "paused" and do not affect ORM calls until the ``new_connections`` block
is exited.

An example of how this API might look::

    async def get_authors(pattern):
        # Create a new context to call concurrently
        async with db.new_connections():
            return [
                author.name
                async for author in Authors.objects.filter(name__icontains=pattern)
            ]

    async def get_books(pattern):
        # Create a new context to call concurrently
        async with db.new_connections():
            return [
                book.title
                async for book in Book.objects.filter(name__icontains=pattern)
            ]

    async def my_view(request):
        # Query authors and books concurrently
        task_authors = asyncio.create_task(get_authors("an"))
        task_books = asyncio.create_task(get_books("di"))
        return render(
            request,
            "template.html",
            {
                "books": await task_books,
                "authors": await task_authors,
            },
        )

This is somewhat verbose, but the goal would be to also add high-level shortcut
functions to enable this kind of behavior (and also to cover over the change
from ``asyncio.ensure_future`` in Python 3.6 to ``asyncio.create_task`` in 3.7).

With this context manager and "sticky threads" within a single connection
context, we then ensure that all code is as safe as we can get it by default;
there is a chance a user could cause a connection to be used within the same
thread for two different parts of a query using ``yield``, but this is already
present today.


Implicit Blocking
~~~~~~~~~~~~~~~~~

The other problem with the ORM design as it stands today is that there are
blocking (network-backed) operations behind model instances, specifically
related fields.

If you get a model instance, and then access ``model_instance.related_field``,
Django will transparently go and fetch the related model's content and return
it to you. This is not possible in async code, however - blocking code must not
run on the main thread, and there is no asynchronous version of attribute
access.

Fortunately, Django already has a way out of this - ``select_related``, which
fetches related fields up front, and ``prefetch_related`` for many-to-many
relationships. If you are using the ORM asynchronously, then we will prohibit
any implicitly blocking operations - like background attribute access, and
instead return an error saying that you should pre-fetch the field.

This has the added benefit of preventing slow code that does N queries in a
``for`` loop, a common mistake for many beginning Django programmers. It does
also raise the barrier to entry because of this, but remember that async Django
will be optional - users will still be able to write synchronous code if they
wish (and will be encouraged to do so in the tutorial, as it is much harder to
get wrong).

``QuerySet``, thankfully, can just implement asynchronous generators and
support both sync and async transparently::

    async def view(request):
        data = []
        async for user in User.objects.all():
            data.append(await extract_important_info(user))
        return await render("template.html", data)

Other Notes
~~~~~~~~~~~

The schema modification parts of the ORM will not be made async; these should
only ever be called from management commands. Some projects do call these within
a view already, but that is not a good idea anyay.


Templating
----------

Templating is currently entirely synchronous, and the plan is to leave it this
way for the near future. Writing an async-capable templating language may be
possible, but it would be a significant amount of work, and deserves its own
discussion and DEP.

It's also notable that Jinja2 already supports asynchronous functionality, so
this may be another good time to look at officially recommending it for some use
cases.

Given this, we will add an async wrapper to the current Django templating
library and its various entry points, but still run the actual template renderer
synchronously. The Jinja2 engine will be updated to use its native async
mode, and documentation will be added to allow third-parties to do the same
if they wish.

We will have to change the template engine signature to include a
``render_async`` method as well as a ``render`` method, with the async variant
being called if it is defined and the template is going to be rendered in
async mode.


Caching
-------

The Django caching abstraction will need to grow an asynchronous variant - the
caching engines are generally what are presented to the user so these will need
to have ``_async`` variants added to them (e.g. ``get_async``, ``set_async``).

Default implementations of these that just call the existing API via
``sync_to_async`` will be provided in ``BaseCache``.

There does not appear to be any risk of overriding thread-safety with the
cache APIs that Django ships, but we should survey third-party cache libraries
and make sure that there is enough machinery to help them if they need it.
The same utilities we write for the ORM will likely help a similar situation
for caches.


Forms
-----

While the basic form library has no need for async support, form validation and
saving are user-overrideable, and both this code as well as several parts of
``ModelForm`` use the ORM to talk to the database.

This means that, at some point, the ``clean`` methods and ``save``, at
minimum, need to be able to be called in an async fashion. Like templating,
however, I believe this is something that is not critical to achieve as part of
a first wave, and so can be addressed with its own working group and DEP.


Email
-----

Email sending is one of the core parts of Django that would most directly
benefit from an asynchronous interface. A ``send_mail_async`` variant of
``send_mail`` can be added, along with ``async`` variants of all the main
email functions (like ``mail_admins``).

This should be one of the most self-contained parts of Django to be converted,
and there are already async-compatible SMTP libraries should we choose to use
them. Again, however, this is lower priority, and can be tackled by itself
separately when the time comes.


Testing
-------

Testing asynchronous applications is tricky, and several parts of Django's test
framework will need updating.

At the base level, raw ASGI applications can be tested with the aid of
``asgiref.testing.ApplicationCommunicator``. This takes care of running an
application's coroutine alongside the test and letting assertions be run on
the output.

The majority of Django's users will use the test client to test their site,
however, and so this will need to be updated to have an asynchronous mode.
Interestingly, this is not a hard requirement - the test client as it is will
be updated to run a natively-async HTTP handling core in its own event loop,
to match the WSGI handler.

The main advantage to having a natively-async test client will be faster
testing, and the ability to inspect coroutines more directly. This means it
should be done eventually, but is not critical to do at the outset.

What is critical, however, is the ability to run tests that are themselves
asynchronous in the first place. Right now this is possible by decorating
a test written as an ``async def`` with ``@async_to_sync``, but this needs
to be properly tested itself and maybe integrated into the Django test runner
better.

There should also be the ability to turn asyncio debug modes (that detect
blocked loops and coroutines that were never started) on during the tests,
and likely also when ``DEBUG=True``. This debug aid merely prints to the
console by default - we need to see if we can make it more explicit to help
our users write safe code.


WebSockets
----------

WebSocket support will not be in Django itself; instead, we will make sure
that Channels has all the hooks it needs to integrate cleanly and take over the
ASGI root app location so it can handle WebSockets itself.

The goal is to not only allow easy offloading of WebSockets to Channels, but
to also allow other apps to be able to take over other protocols that ASGI
servers may provide.


Sequencing
----------

As you can see from the sections above, each feature has its own challenges to
overcome. If we were to tackle these all serially, it would be years until we
even had an initial version of this complete.

However, the ability to add async wrappers around synchronous functions lets
us be far more iterative about the whole thing. There are only really two
core pieces of work that need to be done first - having async views be possible,
and enabling async tests.

Once both these are complete, we can then work on all the other features in
parallel, and release them into Django's ``master`` branch and thus into a
date-based release when they are ready. Even within some features, like the ORM,
we can allow for basic operations to be async-native at first, release that,
and then build the rest with feedback from our users.

The proposed ordering is:

* First round (hopefully in 3.0)

  * HTTP handling, middleware and views (native async with sync wrapper)
  * Async safety and cross-thread usage detection in the ORM
  * Async test support

* Second round (hopefully in 3.1)

  * ORM (async-wrapper interface around existing sync core)
  * Templating (async-wrapper interface around existing sync core)
  * Caching (async-wrapper interface around existing sync core)

* Further individual projects

  * ORM (native async with sync wrappers for backwards compatibility)
  * Caching (native async with sync wrappers)
  * Email
  * Forms

It is crucial not to try and release this as one giant change; we will benefit
far more from it being incremental. There are going to be setbacks along the
way, and ensuring each feature is isolated from the others means those delays
won't compound into each other.

It's also possible that we find it infeasible to make a feature natively-async;
in that case, we should not be afraid to leave it as natively synchronous but
with a supported async wrapper that runs it safely in a threadpool. The goal
is to enable async for the developers who use Django, not to make Django itself
a perfect, async-only project.

Several of the projects mentioned will likely end up with their own DEPs for
implementation, including the caching layer, templating, email, and forms. The
natively-async database layer may also require an async version of DBAPI - this
is something that at least needs some discussion with core Python and maybe a
PEP, though there's been some work towards this already.


Motivation
==========

Software lives in a changing world, and this is maybe the most true about the
Web. Django's current design has served it well for over a decade, and it's
still a great design to handle many of the tasks backend developers need to do;
it powers several billion-dollar companies, and has inspired frameworks in other
languages to adopt similar designs.

We must, however, always think of the future, and how we can help evolve Web
development again. While some of these changes we will never see coming,
asynchronous code is one that has been coming for some time, and we are now
in the middle of it.

Asynchronous code brings with it a way to overcome one of the core flaws of
Python - its inefficient threading. Python webservers must walk a careful line
between enough threads to serve efficiently, and keeping the amount of time
lost context-switching low.

While Python is not a perfect asynchronous language, and there are some flaws
in the core design of ``asyncio``, a community of libraries and modules has
grown up around it, and we benefit from the work of the larger community. At
the same time, it's important we have a plan that delivers our users immediate
benefits, rather than attempting to write a whole new Django-size framework that
is natively asynchronous from the start.

What It Unlocks
---------------

We're not just adding async to Django to make it nebulously "faster" - the goal
is to unlock capabilities that our users - those who develop on top of Django -
simply have not had access to before.

The key part of this is allowing our users to run things concurrently. Be it
database queries, requests to external APIs, or calling out to a series of
microservices, most Django projects have to do concurrent work at some point
during a view.

Very few frameworks have even come close to making concurrency accessible and
safe, and Django has the ability to cross this boundary. If we can make running
database queries concurrently as easy as using Django's ORM is now, we can
raise the bar of what it means to have a framework that lets you write a fast
web app.

The other part to remember is the ability to hold open connections for a long
time without wasting resources. Even without WebSockets, there are still a lot
of long-poll connections, or server-sent-events. Asynchronous Django would allow
our users to write applications to handle these scenarios without having to
think about reverse proxies to offload traffic to while it's waiting.

Sync Still Matters
------------------

It's important to frame this as *adding* async support to Django; we are not
rewriting it, or remove synchronous support. In fact, it is my belief that
synchronous code is safer and easier to write, and that we should encourage it
to be the first way code is written in most cases.

Django has always excelled at being adaptable as sites and projects written
using it grow. Async must factor into that equation; as a Django project
expands, and gets more complex, our users should be able to simply turn to the
async part of our docs and use the same interfaces they know and love to keep
building their project.

If we don't let them mix and match, we lose a lot of the advantage of having
an all-in-one framework like Django, and we raise the barrier to entry too much.

Backwards Compatibility
-----------------------

As always, backwards compatibility is incredibly important. We are never going
to release an "async Django" that our existing users can't take advantage of;
when we do that release, it must come with the traditional release notes, a
couple of small upgrade notes, and pretty much just work.

The amount of rearranging we have to do under the hood to make async work and
be maintainable will make the upgrade a bit trickier than usual for those who
use undocumented Django APIs, but we must do our best to learn from the lessons
of things like the Python 3 migration and ensure that we keep not only the
public APIs backwards-compatible, but also ensure that all the most popular
Django and Python packages continue to work too.

Helping Python
--------------

Python as a programming language community spans a huge range of different
specialities. While traditionally the Web has played a large part in Python's
popularity and usage, other areas - like scientific computing - have grown
a lot in recent years.

Still, though, Django - and the Python web-programming community in general -
have a lot of room to help push Python forward, and bringing a whole new
community of users to asynchronous Python will help it develop and mature
faster. Library support for async is already quite good, but there's nothing
quite as good for a library ecosystem as a whole bunch of sites using async
in production in new and exciting ways.

Bringing on new contributors
----------------------------

I, and many of my fellow long-term Django contributors, cut our teeth writing
a big feature, or by filing a series of patches to fix bugs. As Django has
grown and matured, these opportunities have got fewer and further between.

A large set of new feature work like this provides us ample opportunity to
bring on new contributors and help them get comfortable with contributing -
especially as anyone who contributes, even previous contributors, will have to
get up to speed on async code anyway.

Provided we run the project the right way - and provide places to start
contributing, training, and compensation where we can - we have one of our
largest opportunities in years to grow the Django contributor base (as well as
helping to grow the number of people ready and willing to contribute to async
Python at large).

What is Django?
---------------

Ultimately, we must consider what Django is. If it is what a small group of
developers set out to make at the Lawrence Journal-World all those years ago -
before the rise of the dynamic web, of streaming, of single-page web apps -
then we can likely call it done. Maintain it, polish it, keep it secure, but
ultimately say that it is feature-complete.

If, however, we say that Django's role is to make web development easier, safer
and more enjoyable - even as the Web and programming styles change - then we
must learn to adapt. Async is likely not even the biggest change in that realm;
consider what it might mean to have Django partially run client-side, for
example.

Nonetheless, in an uncertain future, an asynchronous Django is an important
piece of foundational work. It provides us with immediate benefits, but also
lays the groundwork for future change. It's possible in an iterative fashion,
so we can not only deliver it sustainably but also change course if we need to -
making sure that we set the course for the next decade of what the Web becomes.

Rationale
=========

The prospect of an async Django has been raised several times in threads on
django-developers, and the `most recent thread <https://groups.google.com/forum/#!msg/django-developers/Kw7-xV6TrSM/>`_
received close to universal consensus, with some qualms about exact
implementation that this DEP will hopefully answer.

There are several ways to approach the async question, but ultimately this one
has been influenced by several key goals:

* Iterative: This approach allows for regular commits back to the master branch,
  and the ability to release async abilities into Django's fixed releases
  as and when they are ready.

* Backwards-compatibility: Having to keep to Django's existing design pattern
  hinders us from making a nice, clean async framework design, but ultimately
  if we don't do this, we can't call it Django, and people won't use it.

* Sustainable: Async is quite hard to understand, and we have to make sure that
  we not only keep Django possible to maintain, but projects that use Django
  too. This approach uses async where it's needed, but keeps things that are
  perfectly fine being synchronous unchanged.

My work with Channels over the years has also informed some of the ways this
proposal is laid out; various attempts at integrating more closely with Django
views have surfaced many of the problems and solutions laid out above.

That said, there are always going to be problems we never anticipated. This DEP
is less clear on implementation than most, because it must be - as we make
progress towards an async-capable Django, we'll learn more about the problems
we encounter and be able to course-correct.

This way of implementing support may also result in slightly slower performance
for fully-synchronous users. The introduction of asynchronous-native code
into Django is likely to slow down performance for those users who remain on
WSGI and all-synchronous views, as an async loop will have to be started
whenever they need to run code implemented natively in async. The performance
goal here is a drop of 10% or less - if the drop is too severe, we can dedicate
engineering time to improving it. The plan is not to implement async at the cost
of synchronous support.

It's also very much worth thinking about what happens if progress on the project
is abandoned (because of contributors being unavailable, a changing Python
ecosystem, or other reasons). The iterative design means that in this case,
Django is unlikely to end up in a bad state; there might be a few merged changes
that should be reverted, but the intention is to keep Django's policy of the
``master`` branch always being shippable to reduce the impact of such an event.

Besides, even if we just get asynchronous views working and none of the rest of
Django (no ORM, no templates, etc.), this will still be a successful project;
that alone unlocks a lot of potential and unlocks a large amount of the existing
Python asynchronous ecosystem.

The other potential long-term effect of this project is that it might consume
people and energy that could have been used for other Django projects,
essentially "burning out" some contributors. While this is a risk we should
always be aware of, approaching this project with sustainability and funding in
mind will minimise this, and will hopefully turn this project into a large
net positive gain for people and energy instead.


Alternatives
------------

These are some alternative approaches or design decisions that were rejected,
with reasoning why.

Async modules instead of _async functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Instead of the rather ugly suffixing of methods and functions that need both
an async and a sync variant (e.g. ``django.core.cache.cache.get_async``), we
could instead create whole separate async namespaces with things called
by the same name, and just have import paths change::

    from django.core.cache_async import cache
    cache.get("foo")

This is cleaner, but the problem comes when trying to use both sync and async
versions in the same file; it quickly becomes difficult to keep track of what
you are using, and calling the wrong one synchronously may be a difficult bug
to find.

That said, this is one of the decisions that I was closest to going the other
way on; there's still merit here.

Fork Django
~~~~~~~~~~~

A hard fork is unsustainable, and also a massive waste of resources; it's likely
that it would be near-impossible to merge the result back in, given the huge
deviation, and splitting the user and support base is a terrible idea.

For any big refactor like this, the only way to achieve it reliably, especially
in a majority-volunteer community, is to make it incremental, and that means
no hard forks.

Extend Channels
~~~~~~~~~~~~~~~

A popular option people have often suggested is to extend Channels to achieve
many of these goals "external" to Django. Hopefully, if you have read some of
the large amount of text above, you'll see how infeasible it would be to write
this externally; even if we ignored the ORM, maintaining a whole separate
HTTP and middleware path would be very fragile.

Non-asyncio
~~~~~~~~~~~

There are other async frameworks and event loops for Python that are not
``asyncio``, and that have often made better design decisions for the type of
usage that Django wants to do. The ``await`` and ``async`` keywords in Python
are actually independent of the event loop and implementation running underneath
them.

The popularity of ``asyncio``-based libraries, though, makes it the only viable
choice; Django cannot stand alone, we must rely on the research and work of
others to succeed. At the same time, a lot of the restructuring of Django that
is being done would still be applicable to another async solution; if the
situation were to change later on, the work needed to adapt to a different
async runtime would not be nearly as involved as this initial transition.

Greenlets/Gevent
~~~~~~~~~~~~~~~~

It's worth talking about greenlets and Gevent specifically, as they are an
implementation of concurrent Python code that does not use the Python async
syntax.

While the idea of having methods and functions seems attractive at first, there
are many subtle problems with the greenlet-based approach. The lack of an
explicit ``yield`` or ``await`` means that a complex API like Django's basically
becomes unpredictable as to knowing if it will block the current execution
context or not. This then leads to a much higher risk of race conditions and
deadlocks without careful programming, something I have experienced first-hand.

The problems with coroutines sharing database connections mentioned above would
also happen with greenlets. We would have to greenlet-safe the entire Django
ORM and still do something similar to the new-connection-context handler you
see above.

In addition, the third-party support for this style of concurrency is much
weaker. While moving Django to it might cause a "halo effect" and cause a
resurgence in popularity of gevent, this would likely not be enough to support
all the libraries we would need.


Funding
=======

With a project of this size, it is important to consider funding as a crucial
part of the overall implementation of this DEP.

While it is designed to provide value in small iterations - including if it
gets abandoned partway though - the most value comes from having it run as a
single, continuous effort in a relatively short time frame (a year or so).

This means that the project would benefit significantly from someone paid to
both coordinate and contribute code on a part-time or full-time basis. The
Django Fellows are not paid to do work like this - their remit is instead
triage and maintenance - and so we would either need to increase their
funding and time commitment (if they were willing) or, more likely, look
elsewhere.

Previous big initiatives have raised one-off funding - for example, the
Kickstarter campaigns for ``migrations`` and ``contrib.postgres``, and the MOSS
(Mozilla) grant for Channels. With a headline feature like async Django, it is
likely that we could raise a decent amount of money for this project.

It's also worth thinking about *who* can help contribute to this project. Async
is still a relatively new area of Python, and many Django contributors - old
and new - don't have much experience with it. We must budget not only for
people experienced with Django/async to run the project, but also allow for
training and onboarding of contributors.

The nature of the work allows it to be highly parallelizable past the initial
work on the HTTP/middleware/view flow, and so we should make sure that anyone
who is interested can help out as part of a smaller "working group", rather
than having to understand the whole system.

I don't claim to have an answer as to who should run this project, how many
people should be paid, and how they should be paid (be it directly funded like
the Fellows, feature-based contract/bounty work like we did with Channels, or
with part or full time donated from employers who have them on
salary), but I do know that paid contributions will make a large difference.

The project would succeed on volunteer power alone, but it will be a lot slower
and, I expect, a lot less effective at responding to changes and discoveries
along the way, and we may also lose users from Django if it takes too long.


Backwards Compatibility
=======================

The goal is, of course, to have no backwards compatibility issues, and we will
ensure this to the best of our ability on the documented public APIs.

That said, there will likely be small side effects from changing the internals
of the HTTP and middleware path, specifically. Anyone who is using undocumented
APIs in there, including error-reporting and APM integrations, will have to
update their code.

It's worth noting that anyone using Django with async code right now likely
*will* see an incompatibility, as we add more safety around the core components.
Any application that calls the ORM from a coroutine, for example, will cease to
work - but that application was already wrong, as the ORM is fully synchronous,
and the application's event loop would have been totally blocked anyway.


Reference Implementation
========================

This proposal is too large to provide a reference implementation of; it involves
a significant rewrite of Django over multiple years and versions, and any
parallel effort would result in a full Django fork.

That said, most of the base-level code has already been written in the asgiref_
library, including the heavy lifting around testing, thread handling, and
shifting between the sync and async worlds. This library has been an official
Django project for a few years, and will become an install-time dependency of
Django in order to power this change.

There is also considerable prior art in the Channels_ project, which has
managed to bolt several of these concepts onto Django without even being able
to touch Django core code itself.


Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).
