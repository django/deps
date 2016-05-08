==================
DEP 0006: Channels
==================

:DEP: 0006
:Author: Jacob Kaplan-Moss, Andrew Godwin
:Implementation Team: Andrew Godwin et al.
:Shepherd: Andrew Godwin, Jacob Kaplan-Moss
:Status: Draft
:Type: Feature
:Created: 2016-05-08
:Last-Modified: 2016-05-08

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

Historically, Django's request handing has been very simplistic, built around
the concept of requests and responses: the browser makes a request, Django calls
a view, and the view returns a response back to the browser.

However, this architecture is starting to show its age. New protocols —
particularly WebSockets — don't work in this simple round-trip way. Adding
support for these protocols to today's Django apps is can be complicated and
difficult.

Thus, channels. The top-line feature of channels is simple, easy-to-use support
for WebSockets. Channels makes it very easy to write apps that support
WebSockets alongside traditional HTTP views. Notably, channels does not
introduce asyncio, gevent, or any other async code to Django app; all the code
users write runs synchronously in a worker process or thread. This is primarily
an accessiblity play: it's traditionally been very easy to write a "Hello World"
HTTP view; the goal of channels is to make it just that easy to write "Hello
World" WebSockets views.

Under the hood, channels does a fair bit more. In a nutshell, channels replaces
Django's request/response cycle with *messages* that are sent across *channels*.
This means that adding channels to Django enabled not just WebSocket support,
but support for any future protocol (whether uni- or bi-directional). Channels
also allows for background tasks to run out-of-band of the web servers, similar
to some of the feaures of Celery or Python-RQ (though its featureset is far
smaller, and it is not intended to replace most uses of task queues)

Although this is a fairly profound change to Django's internals, it's also fully
backwards-compatible. Django will continue to run under WSGI, and channels
barely touches the WSGI codepaths. Thus, the new features only "appear" when
running Django in "channels mode".

Specification
=============

The section summarizes the basic concepts of channels, shows a simple example,
and explains the implementation plan. This is intended as a high-level overview;
for detailed specifications, documentation, and examples see `the Channels
documentation <https://channels.readthedocs.io/>`_.

Channels Concepts
-----------------

The core of the system is, unsurprisingly, a datastructure called a *channel*.
What is a channel? It is an *ordered, first-in first-out queue* with message
expiry, capacity, and at-most-once delivery to only one listener at a time.

You can think of it as analogous to a task queue - messages are put onto the
channel by producers, and then given to just one of the consumers listening to
that channel.

For more details, see `What is a channel? <https://channels.readthedocs.io/en/latest/concepts.html#what-is-a-channel>`_.

The other key concept is groups, sets of channels that you can send messages
to and get them delivered to all channels in the group. Groups are
network-transparent and look the same across all 

To deploy an app using channels, instead of running a WSGI server, you'll run a
few different things:

* An *interface server* that handles HTTP and WebSocket connections. 

  The interface server is  roughly analgous to the role a WSGI server plays 
  today. `Daphne <https://github.com/andrewgodwin/daphne/>`_ is the default
  (production-ready) implementation [#]_, and for local development
  ``python manage.py runserver`` can act as a (non-production-quality)
  interface-server-and-worker-server-in-one.

* Worker servers that run *consumers* that handle views, websockets, 
  background tasks, etc. 

  You'll run worker servers using ``python manage.py runworker`` [#].

* A *channel layer* that the interface server and consumers communicate
  over. 

  This communication happens using a protocol called 
  `ASGI <https://channels.readthedocs.io/en/latest/asgi.html>`_,  which is 
  similar to WSGI but runs over a network and allows for more protocol types.

  The recommended production-quality channel layer is Redis (via 
  `asgi_redis <https://github.com/andrewgodwin/asgi_redis>`_), but 
  Any channel layer that conforms to the ASGI spec can be used.

.. [#] Daphne is implemented in Python on top of `Autobahn <http://autobahn.ws/>`_ 
       and `Twisted <https://twistedmatrix.com/trac/>`_, and seems to perform
       very well. However, since the interface server runs completely 
       independetly of the worker servers, this implementation can easily be 
       changed without affecting the underlying Django apps.

.. [#] Like the interface server, it's possible for there to be different, 
       non-Django worker implementations. It ought to be fairly trivial to
       implement workers in other Python web frameworks, such as Flask,
       and it may even be possible to implement workers in other languages.

An example app using channels
-----------------------------

To make this concrete, let's look at a simple example app using channels.  The
app is a simple real-time chat app — like a very, very light-weight Slack. There are
a bunch of rooms, and everyone in the same room can chat, in real-time, with
each other using WebSockets. This section will show off the highlights;
for full details see `the code on Github <https://github.com/jacobian/channels-example>`_
and `this article about the app on Heroku's blog <https://blog.heroku.com/archives/2016/3/17/in_deep_with_django_channels_the_future_of_real_time_apps_in_django>`_ [#]_

.. [#] In the intersts of full disclusre, I should state that I (Jacob Kaplan-Moss) 
       was paid by Heroku to write the referenced blog post and example app.

For the most part, this app looks like a normal Django app -- models, views,
templates, URLs, etc. Let's look at the parts that are different:

First, the app needs to define a channel layer in `settings.py`::

    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "asgi_redis.RedisChannelLayer",
            "CONFIG": {
                "hosts": [os.environ.get('REDIS_URL', 'redis://localhost:6379')],
            },
            "ROUTING": "chat.routing.channel_routing",
        },
    }

For more details on channel layers, see the `Channel Layer Types <https://channels.readthedocs.io/en/latest/backends.html>`_ docs.

The channel layer points to our *channel routing* -- a structure that maps
channel names to the functions that handle them::

    # chat/routing.py

    from channels.routing import route
    from . import consumers

    channel_routing = [
        route("websocket.connect", consumers.ws_connect),
        route("websocket.receive", consumers.ws_receive),
        route("websocket.disconnect", consumers.ws_disconnect),
    ]

For more details on channel routing, see the `Channel Routing <https://channels.readthedocs.io/en/latest/getting-started.html#routing>`_ docs.

Here's what one of the consumers looks like::

    # chat/consumers.py

    import json
    from channels import Group
    from channels.sessions import channel_session
    from .models import Room

    @channel_session
    def ws_receive(message):
        label = message.channel_session['room']
        room = Room.objects.get(label=label)
        data = json.loads(message['text'])
        m = room.messages.create(handle=data['handle'], message=data['message'])
        Group('chat-'+label).send({'text': json.dumps(m.as_dict())})

Notice that this looks fairly similar to an HTTP view, except that instead 
of a request in recieves a message, and it doesn't return a response. Channels
are uni-directional, so to send data back to the browser we need to send it
on a *response channel*. In this case, we broadcast to a `group <https://channels.readthedocs.io/en/latest/getting-started.html#groups>`_, which takes care of sending to each
user connected to the room. 

For a full breakdown of these example consumers, see the 
`websocket consumers section of the blog post <https://blog.heroku.com/archives/2016/3/17/in_deep_with_django_channels_the_future_of_real_time_apps_in_django#websocket-consumers>`_.

Finally, we need to deploy this thing using ASGI instead of WSGI. To do that,
we'll create an `asgi.py` [#]_:: 

    import os
    import channels.asgi

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chat.settings")
    channel_layer = channels.asgi.get_channel_layer()

To deploy, we have to run two processes. In the form of a `Procfile <https://honcho.readthedocs.io/en/latest/index.html#what-are-procfiles>`_, these are:

    web: daphne chat.asgi:channel_layer --port 8888
    worker: python manage.py runworker

This is, we run Daphne as an interface server, and ``python manage.py runworker`` 
to handle requests. These processes could be run on different machines, and
we could scale up each type of process separately.

.. [#] Currently, this is *not* generated by ``startproject``; it's an open
       question as to whether that should be changed.

Again, this was just a crash course. For full details, see:

* `Getting Started with Channels <https://channels.readthedocs.io/en/latest/getting-started.html>`_ in the official Channels documentation.
* `The code for the example app <https://github.com/jacobian/channels-example>`_
* `The this article walking through the example <https://blog.heroku.com/archives/2016/3/17/in_deep_with_django_channels_the_future_of_real_time_apps_in_django>`_

Integration plan
----------------

We propose the following integration plan:

* Merge `Channels <https://github.com/andrewgodwin/channels>`_ into Django 1.10.
  Document the channels APIs as "provisional" (using the terminalogy from
  `PEP 411 <https://www.python.org/dev/peps/pep-0411/>`_) so that we have room
  to make API changes. We think changes will be fairly unlikely -- the current
  design represents over two years of design work -- but we should leave the 
  possibilty open.

  This is implemented as `PR #6419 <https://github.com/django/django/pull/6419>`_.

* Keep the other components -- `Daphne <https://github.com/andrewgodwin/daphne>`_,
  `asgiref <https://github.com/andrewgodwin/asgiref>`_
  and `asgi_redis <https://github.com/andrewgodwin/asgi_redis>`_ -- as
  external components [#]_. Since these run independently of Django, they can be
  iterated on separately from Django's release cycle.

* Remove the "provisional" label in Django 1.11 (which is an LTS release)

.. [#] We may want to move these components under the Django github org to 
       signify their "more official" status. Since that's an that's orthagonal
       to the technical work proposed by this DEP, this DEP takes no position 
       on this question.

Motivation
==========

The primary motivation for channels is that of a percieved gap in Django's
abilities; as the Web grows and evolves, the original view-based design has
lasted surprisingly well, but is starting to chafe when presented with some
of the new technologies the web is growing, particularly WebSockets.

Django projects have had to take on external, third-party solutions to try and
fill this hole, whether they are single-use Python servers that proxy into
Django in a variety of ways, or endpoints in entirely different languages
altogether that have more direct first-class support for non-request-response
workflows (such as Node.js or Go).

Every time a Django developer has to go and find a solution, adapt it, or write
their own, Django loses out on the potential for a community of apps, examples
and code around WebSockets that has brought it as far as it has today for
normal HTTP and view code.

Thus, channels' goal is to create a single, unified interface for Django
developers to write their applications against (the consumer and routing model
shown above), and to provide a good abstraction that allows extension and
adaptation of the underlying coordination logic by end-users, specialists, or
the project itself in the future (ASGI).

Like the rest of Django, we cannot hope to satisfy everyone's needs, and in
particular it is unlikely channels could be used as-is at huge scale; however,
no generic component survives that trip, and any resulting code always ends up
very company- and situation-specific.

Moreover, WebSockets are likely the tip of the iceberg; not only does the
growth of connected devices and the "Internet of Things" mean that Django has
to communicate with an ever-growing number of devices with different
communication requirements, but the growth of existing integrations with other
platforms like Slack provides ample opportunity for Django to position itself
as an easy-to-use and reliable solution for all sorts of backend needs.

The core channels design is protocol-agnostic; while it ships with HTTP and
WebSocket support, work is either planned or already underway
for Slack, IRC, email, HTTP/2 and SMS interface servers, allowing developers
to use the same, familiar consumers-and-routing structure to service all kinds
of non-request-response patterns; not just WebSockets.

Channels' end goal is to provide an easy, accessible path for new and existing
Django projects to easily add WebSocket (and other protocol) support in a way
that performs well at small and medium scales, and which cleanly gets out of
the way and leaves you with a good abstraction to build upon once you reach
large scale.

We should not lose sight of the fact that one of our jobs as a framework is
to choose tradeoffs for our users and present them with a single, cohesive
approach that helps inform good project architecture and foster a community of
third-party solutions, extensions and additions to the code; without things
like a standardised view, middleware, model information and settings system,
Django would not be where it is today. Channels takes that to the next missing
component - the "real-time", evented web, and provides a design model that is
a balance between flexible and rigid, trying to match the Django philosophy
as close as possible.

Rationale
=========

There are several obvious alternatives to channels that could be taken, and
some major decisions in its design that have at first glance equally viable
alternatives. This section tries to address some of the more important ones.

In-process async/asyncio
------------------------

Python has had in-process async support for some time with solutions like
Twisted and gevent, and with the introduction of ``asyncio`` in Python 3,
an officially-blessed solution, too.

Putting Django's Python 2 compatability requirement aside, the main argument
against using these for this design was one of both feasibility and 
developer-friendliness. Making the entirely of Django run asynchronously would
have been a huge challenge; we have over a decade of synchronous code, and
going through all of it to fix and audit it would have taken a multi-year
effort on the part of many developers, resources Django is unlikely to have
in the near future.

Developer-friendliness comes in when we ask new or async-inexperienced
programmers to jump in and write async code as part of even their first
"hello world" WebSocket example; due to the way Python async works, we would
have to provide parallel sync and async versions of most of the API if we
were to maintain backwards compatibility, meaning developers would have to
sit down and slowly work out what to use in which case (with a failure case -
using synchronous code in an async context, or setting yourself up for occasional
deadlocks or livelocks - that is not immediately apparent
and can in fact silently live in a codebase for months or years until it causes
performance problems).

Channels tries to take the benefit of Python's async support, and apply it in
the interface servers, which run as 100% asynchronous code, but separately from
the user's main business logic. There's nothing preventing advanced users from
writing their own interface or worker servers that do highly-asynchronous
operations using an entirely async stack - one can imagine a custom worker
server that did parallel fetches on APIs, for example - but we should not force
this into the basic abstraction users have to work with, and instead provide
something familiar, safe, and that performs reasonably well.

At-most-once delivery
---------------------

Channels' core abstraction, the channel, has at-most-once delivery. This choice
is one side of a binary choice that all queue systems must make; at-most-once,
or at-least-once.

The situations that channels will actually drop messages in are quite small;
mostly, they revolve around servers unexpectedly dying, or inordinate amounts
of traffic filling up the channel capacity. In general, day-to-day use, users
would likely see less than 0.01% of messages dropped.

The choice of delivery guarantee informs the design of the rest of the solution,
as well. With at-most-once, we will have to allow for retry logic and coding
to cope with failure - something Django developers are very used to given the
non-guaranteed nature of HTTP and browsers. If we were to have chosen
at-least-once, however, we would have had to introduce a whole deduplication
system and try and educate developers that their consumer code might be run
multiple times per message, on different worker machines; a situation the
Django community has less experience dealing with and which is arguably harder
to resolve in a system that also deals with HTTP's dropped connections and
request queue overloads.

Network transparency
--------------------

The channel layer is, by design, network-transparent; that is, all worker
and interface servers in the same deployment see the same channels and groups.

This introduces what may seem like unnecessary complexity, but it addresses
a key scaling problem that any project that grows past a single node must
consider - broadcast. Many applications for channels, such as chat systems,
notifications, live blogs and status GUIs, require the ability to send messages
to an end-user WebSocket (or other open socket) from any number of places in
the system - model code, consumers on other sockets, CLI tools, etc.

Without the network transparency, we would have had to build a separate
infrastructure to enable the transport of these messages around, as well as
a second abstraction just for these cross-network messages. Routing large
broadcast messages to large groups of connected sockets would likely have been
very inefficient in terms of network traffic without the interface servers also
understanding the network routing system at a higher level.

Thus, the network transparency is built-in to channels at the core, allowing
not only broadcast but a host of other useful features, like the ability to
dedicate and tune machines to a single role (interface, worker, or worker on
specific channels), and the lack of requirement for session stickiness.

Small-scale deployments that only run on a single machine can still use a
machine- or process-local channel backend, and channels comes with one of each;
scaling down is important, too.

The ASGI specification, which defines the channel and group transport channels
uses, is designed to only impose as many guarantees and provide just enough API
that it can be sensibly built against while allowing flexibility in
implementation; writing a network-transparent channel layer is difficult, but
not tying Django to a single one and decoupling it like this allows both
iteration on the one or two preferred solutions, and lets large companies or
projects built out their own to suit their specific needs.

Multi-listener ordering
-----------------------

While channels guarantees ordering of messages on a channel when there is a
single listener - for example, when an interface server is reading a response
body to send back to a connected client - it does not guarantee global ordering
or mutually exclusive consumer execution when there is more than one connected
listener.

This is not a problem for listeners to channels like ``http.request``; all of
the consumers run on the messages in that channel are entirely independent and
can run simultaneously. It becomes an issue for channels like
``websocket.receive`` where a client is sending WebSocket frames rapidly, such
that several different workers pick messages off the queue from the same client
before others have finished executing.

Solving this problem in a general way in a networked system is impossible to
do without a significant performance hit, either by coordination or session
stickiness. For this reason, channels leaves the non-global-ordering,
simultaneous style as the default, and provides a decorator, ``enforce_ordering``,
that provides one of two levels of ordering and exclusivity guarantees at
different levels of performance degredation.

Alternatives
------------

There are many alternative architectures to the ones proposed by this DEP, and
each has their advantages and disadvantages. Channels does not intend to make
it impossible to use these; indeed, if someone wishes to run an
evented system, it is designed so that the message formats, consumer and
routing abstraction is re-useable.

However, based on several years of prototypes, design work, and the existing
design of Django, it is the authors' belief that this design represents the
best set of compromises for the large majority of current and future Django
projects.


Backwards Compatibility
=======================

Channels is fully backwards-compatible. Until you switch into ASGI mode by
deploying an interface server and running workers, Django continues to use
the WSGI codepaths. This means that performance under WSGI is unchanged
by the introduction of channels.

The underlying architecture *does* change substantially after switching into
ASGI mode, but that's an explicit opt-in step, and thus has no backwards-
compatibilty concerns.

Reference Implementation
========================

See:

* The `Channels app <https://github.com/andrewgodwin/channels>`_, and
  the proposed merge into Django as `PR #6419 <https://github.com/django/django/pull/6419>`_.

* `Daphne <https://github.com/andrewgodwin/daphne>`_ - the interface server.

* `asgiref <https://github.com/andrewgodwin/asgiref>`_ - reference ASGI implementations.

* `asgi_redis <https://github.com/andrewgodwin/asgi_redis>`_ - Redis ASGI implementation

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).

(All DEPs must include this exact copyright statement.)
