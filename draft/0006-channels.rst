==================
DEP 0006: Channels
==================

:DEP: 0006
:Author: Jacob Kaplan-Moss
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

Thus, Channels. The top-line feature of Channels is simple, easy-to-use support
for WebSockets. Channels makes it very easy to write apps that support
WebSockets alongside traditional HTTP views. Notably, Channels does not
introduce asyncio, gevent, or any other async code to Django app; all the code
users write runs synchronously in a worker process or thread. This is primarily
an accessiblity play: it's traditionally been very easy to write a "Hello World"
HTTP view; the goal of Channels is to make it just that easy to write "Hello
World" WebSockets views.

Under the hood, Channels does a fair bit more. In a nutshell, Channels replaces
Django's request/response cycle with *messages* that are sent across *channels*.
This means that adding Channels to Django enabled not just WebSocket support,
but support for any future protocol (whether uni- or bi-directional). Channels
also allows for background tasks to run out-of-band of the web servers, similar
to some of the feaures of Celery or Python-RQ (though its featureset is far
smaller, and it is not intended to replace most uses of task queues)

Although this is a fairly profound change to Django's internals, it's also fully
backwards-compatible. Django will continue to run under WSGI, and Channels
barely touches the WSGI codepaths. Thus, the new features only "appear" when
running Django in "Channels mode".

Specification
=============

The section summarizes the basic concepts of Channels, shows a simple example,
and explains the implementation plan. This is intended as a high-level overview;
for detailed specifications, documentation, and examples see `the Channels
documentation <https://channels.readthedocs.io/>`_.

Channels Concepts
-----------------

The core of the system is, unsurprisingly, a datastructure called a *channel*.
What is a channel? It is an *ordered, first-in first-out queue* with message
expiry and at-most-once delivery to only one listener at a time.

You can think of it as analogous to a task queue - messages are put onto the
channel by producers, and then given to just one of the consumers listening to
that channel.

For more details, see `What is a Channel? <https://channels.readthedocs.io/en/latest/concepts.html#what-is-a-channel>`_.

To deploy an app using Channels, instead of running a WSGI server, you'll run a
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

An example app using Channels
-----------------------------

To make this concrete, let's look at a simple example app using Channels.  The
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
  Document the Channels APIs as "provisional" (using the terminalogy from
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
       to the technical work proposed by this PEP, this PEP takes no possition 
       on this question.

Motivation
==========

TODO:
- background
- "real-time web" and looking forward (apps, new protocols)
- accessibilty play

Rationale
=========

TODO:
- why channels?
- not async because....
- altneratives

Backwards Compatibility
=======================

Channels is fully backwards-compatible. Until you switch into ASGI mode by
deploying an interface server and running workers, Django continues to use
the WSGI codepaths. This means that performance under WSGI is unchanged
by the introduction of Channels.

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
