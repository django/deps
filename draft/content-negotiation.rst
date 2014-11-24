Content Negotiation Improvements
=================================

Created: 2014-04-14
Author: Mark Lavin
Status: Draft

Overview
=================================

Define additional hooks and utilities in the request/response cycle to manage
content negotiation with HTTP clients.

Rationale
=================================

Django provides a number of utilities for parsing form-urlencoded data and rendering
HTML templates. This fits a large use case for people building websites with Django.
As more users look to use Django to build webservices they have to deal with
`content negotiation <http://www.w3.org/Protocols/rfc2616/rfc2616-sec12.html>`_ without
similar utilities. Currently any parsing of a request body when the Content-Type
is not application/x-www-form-urlencoded or multipart/form-data is left up to the
user's application. Similarly handling requests which do not Accept text/html is
again left up to the user. Without some of the basic utilities in Django, users
instead look to external applications such as django-rest-framework, django-tastypie,
piston, django-nap or any number of applications from https://www.djangopackages.com/grids/g/api/.
Most of these reuseable applications have invented their own method for handling
this problem and each could benefit from standardization in this area while continuing
to provide utilities in related areas such as how resources are defined, linked
and validated. These applications will serve as a place for Django to start
on its implementation, building off of what is known to work in production and
improving where it can given its ability to potentially modify or clean up internal
APIs which could not otherwise be changed by a third party application.

This has been discussed before on django-developers

- `Proposal: better support for generating rest apis in django core <https://groups.google.com/d/msg/django-developers/Qr0EorpgYKk/W28GwS1qLe0J>`_
- `Support POST of application/json content type <https://groups.google.com/d/msg/django-developers/s8OZ9yNh-8c/yWeY138TpFEJ>`_

On each occasion Tom Christie, author of Django Rest Framework, chimed in with his
insight and support of the idea. He also created a ticket with a minimal proposal
which was accepted in https://code.djangoproject.com/ticket/21442. Some initial
work has been started by him https://github.com/tomchristie/django/tree/ticket_21442

Implementation
=================================

The proposed implementation builds off of the proposal from #21442

Request Parsing
---------------------------------

The main changes proposed are as follows:

- Define an API for parsing incoming request bodies and registering them with the framework
- Break out the urlencoded and multipart parsers from HttpRequest according to this API
- Define a new ``request.data`` to be used by the parsing framework for the deserialized body

Similar to the current `upload handlers <https://docs.djangoproject.com/en/stable/topics/http/file-uploads/#upload-handlers>`_
this request body parsing needs to be handled at the request level. Rather than introducing a new setting,
the proposed change is to add hooks to the ``HttpRequest`` class and ``WSGIHandler`` instance
(exposed via ``get_wsgi_application``) to register additional handlers.

.. code-block:: python

    # wsgi.py

    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "example.settings")

    # This application object is used by any WSGI server configured to use this
    # file. This includes Django's development server, if the WSGI_APPLICATION
    # setting points here.
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    application.register_body_parser(json_parser)

Internally this will update the ``request_class`` on the ``WSGIHandler`` instance to register the parser
callable.

.. code-block:: python

    class HttpRequest(object):
        """A basic HTTP request."""
    ...
        _body_parsers = [
            MultiPartParser,
            FormEncodedParser,
        ]

        @classmethod
        def register_body_parser(cls, parser):
            cls._body_parsers(parser)

        @property
        def body_parsers(self):
            return self._body_parsers
    ...

    class WSGIHandler(base.BaseHandler):
    ...
        request_class = WSGIRequest
    ...
        def register_body_parser(self, parser):
            self.request_class.register_body_parser(parser)

This requires refactoring the existing ``multipart/form-data`` and ``application/x-www-form-urlencoded`` parsing
functions to match the new API. The API of the parsers will be documented an public but the internals
of ``WSGIHandler`` would remain private. Similar to the upload handlers, the parsers could be changed
on a per-request basis but only if the body has not already been parsed (i.e. in a middleware
prior to the CSRF middleware).

Third-party libraries which wish to easily ship new parsers and register them can be
handled via the equivalent of a WSGI middleware.

.. code-block:: python

    from django.core.wsgi import get_wsgi_application
    from restframework.wsgi import RestParserApplication
    application = RestParserApplication(get_wsgi_application())


Response Types
---------------------------------

The main changes proposed are as follows:

- Define an emitter framework for generating responses from data based on content type
- Allow emitters to be registered for use in negotiating responses
- Define a ``HttpResponse`` subclass which consumes view defined data which will be transformed by the negotiated emitter

The approach here would also be modeled after an existing pattern namely the ``TemplateResponse``. A new subclass of ``HttpResponse``
would be added called ``NegotiatedResponse`` which takes data to be serialized based on the negotiated content type.
Like ``TemplateResponse``, ``NegotiatedResponse`` will used a delayed rendering approach so that response
processing middleware will have the chance to modify the content or content type prior to data
being serialized for the final response content.

.. code-block:: python

    class NegotiatedResponse(HttpResponse):

        def __init__(self, content, emitter, content_type=None, status=None, reason=None):
            ...

The ``emitter`` argument represents a callable which will transform the passed ``content`` to
final response body at the end of the rendering stage. Again the middleware stack will have a chance
to modify this ``emitter``.

Rather than have users set this ``emitter`` and ``content_type``, typically instances of ``NegotiatedResponse``
will be created from the current ``request.negotiate_response`` which sets the ``emitter`` and ``content_type`` based
on the current ``Accept`` headers and returns a usable ``NegotiatedResponse`` instance.

.. code-block:: python

    def my_view(request):
        return request.negotiate_response({'message': 'Hello World'})

Similar to the request body parsing, this requires that emitters are registered with the request class related
to particular content types.


Open Questions and Challenges
---------------------------------

- At what level should these parsers/serializers be defined? Globally? Per request/view?
- What additional parsers, if any, should be included in Django?
- What initial serializers, if any, should be included in Django?

Copyright
=================================

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed)
