==================================
DEP 182: Multiple Template Engines
==================================

:DEP: 182
:Type: Feature
:Status: Accepted
:Created: 2014-09-14
:Last-Modified: 2014-12-28
:Author: Aymeric Augustin
:Implementation-Team: Aymeric Augustin
:Shepherd: Carl Meyer
:Django-Version: 1.8
:Resolution: Accepted


Abstract
========

Support some alternate template engines such as Jinja2_ out of the box.

Keep the Django Template Language as the default template engine.

Provide a stable API for integrating third-party template engines.

Support multiple template engines within the same Django project.


Motivation
==========

The Django Template Language (DTL) is `quite opinionated`_. It is purposefully
designed to limit the amount of logic that can be embedded in templates. This
choice keeps business logic outside of templates. Sometimes it also pushes
display logic into views.

Custom logic can be expressed through custom template filters or tags. APIs
such as simple_tag_, inclusion_tag_ and assignment_tag_ make common use cases
easier. Still, writing custom template tags can be hard. Often it results in
messy code.

Furthermore the DTL can be slow to render complex templates. While this isn't
an issue for many simple websites, complex pages may suffer from the cost of
interpreting templates in Python. Poor performance has blocked efforts to
introduce `template-based widget rendering`_, leaving Django forms stuck with
concatenating hardcoded pieces of HTML in Python.

PyPy improves rendering speed a lot. However, in 2014, PyPy isn't ready for
being recommended as Django's default deployment platform. Its support for
Python 3 is still experimental. PyPy is still a second-class citizen of the
Python ecosystem. For instance, well-known Linux distributions don't ship a
WSGI server running on PyPy out of the box.

Finally, attempts to optimize rendering performance `have failed`_.

For at least these two reasons, convenience and performance, Django users are
increasingly turning to alternate template engines. Jinja2 is the most popular
choice thanks to its syntax inspired by the DTL and its excellent performance.

Given Django's `loose coupling`_ philosophy, it is relatively easy to swap the
template engine. However seamless integration requires a non-trivial amount of
code. For example `half a dozen libraries`_ compete for providing integration
between Django and Jinja2.

Therefore, this DEP proposes:

1. to define a formal API for integrating third-party template engines
2. to provide built-in support for  `template strings`_ and Jinja2_


Rationale
=========

General architecture
--------------------

The operation of a template engine can be split in three steps:

1. Configure: set options that will affect the following two steps
2. Load: find the template for a given identifier and preprocess it
3. Render: process the template with a context and return a string

When this document discusses configuring, loading or rendering, it refers to
these steps or to their implementation.

General principles
------------------

The Django Template Language hasn't evolved much over the years. It carries
several design decisions made in 2005. Nine years later, if the Django team
started from a clean slate, it would make different decisions.

Therefore this project avoids encoding the legacy of the DTL in APIs. It
doesn't encourage third-party engines to provide compatibility with the DTL.
Instead it focuses on integration with other components of Django.

Maintainers of third-party engines are welcome to make almost any design
decision they want. The main exception is security. This DEP is prescriptive
when it comes to security considerations:

* HTML autoescaping is required by default to defend against XSS attacks
* integration with Django's CSRF protection framework is mandatory

Built-in engines
----------------

Supporting pluggable engines is a strategy that has served Django well in many
areas. It's more valuable in the long term than just merging a mature Django -
Jinja2 adapter.

The Django Template Language must remain the default to avoid creating a huge
backwards incompatibility without an acceptable upgrade path for the ecosystem
at large.

Support for template strings is built-in to validate a minimal implementation.
This is akin to the local memory cache backend or, to a lesser extent, to the
SQLite database backend.

Support for Jinja2 is built-in because it appears to be the most widely used
alternative. No one asked for built-in support for another engine when this
DEP was discussed.

Support for other template engines is expected to be provided by third-party
libraries. The reasons for doing so are exactly the same as for the cache and
database engines.

Engine selection
----------------

Developers must be able to select the most appropriate engine for each page
e.g. use Jinja2 only for a few performance-intensive pages. Also this provides
a better migration story for converting a website from one engine to another.
That's why Django must support several template engines within the same
project.

If several template engines are configured, when tasked with rendering a given
template, Django must choose one. There are at least four ways to do this:

1. Explicitly selecting an engine, for example:

   .. code:: python

       html = render_to_string('index.html', context, using='jinja2')

   Not only does this add some inconvenient boilerplate, regardless of the API
   that's chosen, but worse, each view requires a particular template engine.
   A developer integrating a third-party application finds themselves unable
   to replace built-in templates with templates written for another engine.

2. Explicitly tagging templates, for example:

   .. code:: jinja

       {# language: jinja2 #}

   This works like charset declaration in Python modules. Unfortunately, due
   to the way template engines are implemented, Django would have to locate
   the template, figure out which engine it uses, and then the engine would
   locate the template again, load it and render it. That would restrict
   engines to selection mechanisms that Django implements and introduce an
   unhealthy amount of duplication as well as a risk of inconsistencies.

3. Convention: the file extension would define which engine to use. That's a
   pragmatic solution. Ruby on Rails would likely take this route.

   However, since the Django ecosystem favors configuration over convention,
   most Django - Jinja2 bridges provide a setting that controls which
   templates must be rendered with Jinja2. That setting defines a regular
   expression against which template names are tested.

   If extensions are configurable, there's a risk that pluggable apps will end
   up with incompatible requirements. For example, if app A wants ``.html``
   files to be rendered with the DTL and app B wants them to be rendered with
   Jinja2, it becomes impossible to use both apps in the same project. A
   configuration mechanism that handles such cases would be too complex.

   If extensions are enforced, some users will be have to use file names that
   they don't like or that their editors don't handle well. The potential for
   bikeshedding makes this an unattractive option. Finally template loaders
   that don't store templates in the filesystem may use identifiers without a
   file extension.

4. Trial and error: in order to load a template, Django would iterate over the
   list of configured template engines and attempt to locate the template with
   each of them until one succeeds.

   Since there's no way to ascertain whether a particular file is intended for
   a given template engine, engines that load templates from the filesystem
   should search for templates in distinct locations. Each engine must have
   its own list of directories to load templates from and these lists mustn't
   overlap.

   As a consequence, a convention would still be necessary to give each engine
   its own subdirectory within installed applications to load templates from.
   This should simply be the engine's name e.g. ``/jinja2/`` for Jinja2. In
   order to preserve backwards-compatibility, it would remain ``/templates/``
   for the DTL. This convention has a lower impact on users because editors
   don't care about directory names the same way they do about file
   extensions.

   In a project that is developed so that only one engine will find a template
   with a given identifier, the order of template engines doesn't matter.
   However it's also possible to rely on this order to implement fallback
   schemes. For instance, if a pluggable application uses the DTL, a developer
   can provide Jinja2 replacements for its templates by putting Jinja2 before
   the DTL in the ``TEMPLATES`` setting described below.

Option 4 appears to provide the best compromise. It isn't perfect but it beats
the alternatives and it doesn't have any drawbacks for daily use. It creates a
healthy separation between templates designed for each engine.

In addition, option 1 will be provided because it gives developers low-level
control for atypical use cases. They can implement their own scheme if option
4 doesn't work for them. It won't add much complexity to the implementation.

Configuring
-----------

Template engines are configured in a new setting called ``TEMPLATES``. Here's
an example showcasing all possibilities:

.. code:: python

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'APP_DIRS': True,
        },
        {
            'BACKEND': 'django.template.backends.jinja2.Jinja2',
            'DIRS': [os.path.join(BASE_DIR, 'jinja2')],
            'OPTIONS': {
                'extensions': ['jinja2.ext.loopcontrols'],
            },
        },
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'NAME': 'fallback',
            'DIRS': [os.path.join(BASE_DIR, 'fallback_templates')],
        },
    ]

The structure bears some similarity with ``DATABASES`` and ``CACHES`` but it's
a list rather than a dict because the order matters in some cases.

``BACKEND`` is a dotted Python path to a template engine class implementing
Django's template backend API as specified below.

``NAME`` must be unique across configured template engines. It's an identifier
that allows selecting an engine for rendering. It defaults to the name of the
module defining the engine class i.e. the penultimate piece of ``BACKEND``.

Since most engines load templates from files, the top-level configuration for
each engine contains two normalized settings:

* ``DIRS`` works like Django's current ``TEMPLATE_DIRS``. It defaults to the
  empty list (``[]``).
* ``APP_DIRS`` tells whether the engine should try to load templates from
  conventional subdirectories inside applications. It defaults to ``False``.

``APP_DIRS`` is a boolean rather than the name of the subdirectory because
that name is a property of the template engine, not a property of the project.
It must be shared by all applications for interoperability of pluggable apps.

Engine-specific settings go inside an ``OPTIONS`` dictionary which defaults to
``{}``. The intent is that they will be passed as keyword arguments when
initializing the template engine.

Loading
-------

Loading and rendering look like they could be handled independently, but
they're coupled as soon as a template extends or includes another one, as the
renderer needs to call the loader. Thus Django must have each template engine
configure and use its own loading infrastructure.

With its default settings, Django loads templates from directories listed in
the ``TEMPLATE_DIRS`` setting and from the ``'templates'`` subdirectories
inside installed applications. The latter allows pluggable applications to
ship templates.

These basic features should be provided by all template engines according to
the values of ``DIRS`` and ``APP_DIRS``. Each engine should define a
conventional name for the subdirectory contaning its templates inside an
installed application. Django searches templates first in directories listed
in ``DIRS`` and then in installed applications if ``APP_DIRS`` is ``True``.

If an engine can't support these features, it must raise an exception when
it's configured with a non-empty ``DIRS`` or with an ``APP_DIRS`` set to
``True``.

At their discretion, engines may provide:

* more flexibility for configuring the directories templates are loaded from
  and their order of precedence
* other options such as loading templates from Python eggs or from a database
* performance optimizations like caching templates when they're first loaded

Such engine-specific features are configured in ``OPTIONS``.

Rendering
---------

Template engines must provide automatic HTML escaping to protect against XSS
attacks. It must be enabled by default for two reasons:

* security should be the default
* that's Django's historical behavior

Autoescaping is disabled by default in Jinja2, leaving it up the developer to
define which variables need escaping and favoring performance over security.
The Django adapter will reverse this default.

If an object provides an ``__html__`` method, template engines should assume
that it can be used to get a safe HTML representation of the object. The
result is guaranteed to be convertible into a ``str`` on Python 3 and a
``unicode`` on Python 2 but it may be a subclass. This convention provides
interoperability between ``django.utils.safestring`` and template engines.

Furthermore, when a template is rendered with a reference to the current
``request``, for instance by using the ``render`` shortcut, template engines
must make the CSRF token available in the context, ideally with an equivalent
of Django's ``{% csrf_token %}`` tag.

This makes it less likely that developers encounter problems with the CSRF
protection framework and choose to simply disable it.

Internationalization
--------------------

There are two sides to internationalizing templates:

1. marking strings for translation
2. extracting translatable strings

The former isn't an issue. Each template engine can provide a wrapper for the
functions from ``django.utils.translation`` or recommend an idiomatic way to
invoke them.

The latter is more involved because the current implementation of the
``makemessages`` management command is inflexible in three ways — see the
appendix for details:

* All files found in the current working directory are treated identically
* Any file that isn't a Python module is assumed to be written in the DTL
* Extraction algorithms are hardcoded in ``django.utils.translation``

Ideally each template engine will provide a list of template files it can
handle and implement a suitable extraction process for translatable strings.
However this raises several questions.

* What will the API look like? Considering the ad-hoc nature of the current
  code of ``makemessages``, it's hard to answer this question without trying
  to implement an API and seeing how it turns out.
* How feasible is it for template engines to provide a relevant list of their
  template files? How should applications installed outside of the current
  working directory be handled? This may warrant provisions for customizing
  the set of files to extract strings from.
* Can backwards-compatibility be preserved for most use cases? This proposal
  requires properly configured template engines while the current code can run
  without settings. An option to enable "legacy mode" and preserve the
  historical behavior of ``makemessages`` may help.

An alternative would be to switch to Babel_ for extracting translatable
strings. It would solve the problems described above at the cost of adding an
optional dependency. ``makemessages`` would become a wrapper around Babel and
invoke it with an appropriate configuration. This option will be considered
and may be chosen during the implementation phase.

Management commands
-------------------

The ``startapp`` and ``startproject`` management commands won't support
alternative template engines for now. While it would be feasible to add a
``--backend/-b`` option, it would only support built-in backends, because
these commands run without configured settings. That makes the feature less
attractive.


Specification
=============

Backends API
------------

The entry point for a template engine is the class designated by the
``'BACKEND'`` entry in its configuration.

This class must inherit ``django.template.backends.BaseEngine`` or implement
the following interface.

.. code:: python

    from django.core.exceptions import ImproperlyConfigured


    class BaseEngine(object):

        # Core methods: engines have to provide their own implementation
        #               (except for from_string which is optional).

        def __init__(self, params):
            """
            Initializes the template engine.

            Receives the configuration settings as a dict.
            """
            params = params.copy()
            self.name = params.pop('NAME')
            self.dirs = list(params.pop('DIRS'))
            self.app_dirs = bool(params.pop('APP_DIRS'))
            if params:
                raise ImproperlyConfigured(
                    "Unknown parameters: {}".format(", ".join(params)))

        @property
        def app_dirname(self):
            raise ImproperlyConfigured(
                "{} doesn't support loading templates from installed "
                "applications.".format(self.__class__.__name__))

        def from_string(self, template_code):
            """
            Creates and returns a template for the given source code.

            This method is optional.
            """
            raise NotImplementedError(
                "subclasses of BaseEngine should provide "
                "a from_string() method")

        def get_template(self, template_name):
            """
            Loads and returns a template for the given name.

            Raises TemplateDoesNotExist if no such template exists.
            """
            raise NotImplementedError(
                "subclasses of BaseEngine must provide "
                "a get_template() method")

        # Internationalization methods (tentative).

        def extract_from_dir(dirname=None, **options):
            """
            Extract messages from template files found in the given directory.
            """
            # The default implementation will build upon the find_files and
            # prepare_for_xgettext methods defined below and xgettext itself.

        def find_files(self, dirname, followlinks=False):
            """
            List template files found in the given directory.
            """
            # The default implementation will walk directories pointed to by
            # DIRS and APP_DIRS if they're under dirname and return all files
            # found in these directories.

        xgettext_target_language = "Python"

        def prepare_for_xgettext(self, template_code, **options):
            """
            Transform template code into something xgettext accepts as Python.

            The target language is defined by xgettext_target_language.
            """
            raise NotImplementedError(
                "subclasses of BaseEngine must provide "
                "a prepare_for_xgettext() method")

Template objects returned by backends must conform to the following interface.

.. code:: python

    from django.template.backends.utils import csrf_input_lazy, csrf_token_lazy


    class BaseTemplate(object):

        def render(self, context=None, request=None):
            """
            Render this template with a given context.

            If context is provided, it must be a dict.

            If request is provided, it must be a ``django.http.HttpRequest``.
            """
            if context is None:
                context = {}
            if request is not None:
                # Passing the CSRF token is mandatory. Helpers are available.
                context['csrf_input'] = csrf_input_lazy(request)
                context['csrf_token'] = csrf_token_lazy(request)
                # Passing the request is optional. As Django doesn't have a
                # global request object, it's useful to put it in the context.
                context['request'] = request

            raise NotImplementedError(
                "subclasses of BaseTemplate must provide a render() method")

``Engine`` and ``Template`` classes in adapters should wrap corresponding
classes from the underlying libraries rather than inherit them in order to
minimize the risk of name clashes.

Template backends must be thread-safe.

Django backend
--------------

Refactoring
~~~~~~~~~~~

The Django Template Language will be refactored into a standalone library.

It will encapsulate its runtime configuration into an instance of a
``DjangoTemplates`` class.

Context processors will be moved from ``django.core.context_processors`` to
``django.template.context_processors`` with a deprecation period. Since users
will have to write a new ``TEMPLATES`` setting, it's a good time to clean up
this historical anomaly.

Settings
~~~~~~~~

Here's the default configuration for the Django backend:

.. code:: python

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'NAME': 'django',
            'DIRS': [],
            'APP_DIRS': False,
            'OPTIONS': {
                'allowed_include_roots': [],
                'context_processors': [],
                'loaders': None,
                'string_if_invalid': '',
            },
        },
    ]

When the ``'LOADERS'`` option isn't set, Django configures:

* a ``filesystem`` loader configured with ``DIRS``
* an ``app_directories`` loader if and only if ``APP_DIRS`` is ``True``

When the ``'LOADERS'`` option is set, Django:

* accounts for ``DIRS`` if and only if the ``filesystem`` loader is included
* expects ``APP_DIRS`` to be ``False`` and raises an ``ImproperlyConfigured``
  exception otherwise

If ``TEMPLATES`` isn't defined at all, for the duration of a deprecation
period, Django will automatically build a backwards compatible version as
follows:

.. code:: python

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': settings.TEMPLATE_DIRS,
            'OPTIONS': {
                'allowed_include_roots': settings.ALLOWED_INCLUDE_ROOTS,
                'context_processors': settings.TEMPLATE_CONTEXT_PROCESSORS,
                'loaders': settings.TEMPLATE_LOADERS,
                'string_if_invalid': settings.TEMPLATE_STRING_IF_INVALID,
            },
        },
    ]

Jinja2 backend
--------------

Packaging
~~~~~~~~~

Jinja2 will become an optional dependency of Django.

Settings
~~~~~~~~

Here's the default configuration for the Jinja2 backend:

.. code:: python

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.jinja2.Jinja2',
            'NAME': 'jinja2'
            'DIRS': [],
            'APP_DIRS': False,
            'OPTIONS': {
                'environment': 'jinja2.Environment',
            },
        },
    ]

The main option is ``'environment'``. It's a dotted Python path to a callable
returning a Jinja2 environment. It defaults to ``'jinja2.Environment'``.
Django invokes that callable and passes other options as keyword arguments.
Furthermore, Django uses defaults that differ from Jinja2's for a few options
if they aren't set explicitly:

* ``'autoescape'``: ``True``
* ``'loader'``: a loader configured for ``DIRS`` and ``APP_DIRS``
* ``'auto_reload'``: ``settings.DEBUG``
* ``'undefined'``: ``DebugUndefined if settings.DEBUG else Undefined``

Here's an example that uses the default settings and adds a few utilities to
the global namespace:

.. code:: python

    # <project_name>/jinja2.py

    # Django should provide a public API for this purpose.
    from django.contrib.staticfiles.storage import staticfiles_storage
    from django.core.urlresolvers import reverse

    from jinja2 import Environment

    def environment(**options):
        env = Environment(**options)
        env.globals.update({
            'reverse': reverse,
            'static': staticfiles_storage.url,
        })
        return env

The ``'environment'`` option would be set to
``<project_name>.jinja2.environment``.

Dummy backend
-------------

This backend is built on top of `Template strings`_. It's a proof of concept.

It doesn't accept any options. Its configuration looks as follows:

.. code:: python

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.dummy.TemplateStrings',
            'NAME': 'dummy',
            'DIRS': [],
            'APP_DIRS': False,
        },
    ]

Shortcuts
---------

The current public APIs are:

* ``render(request, template_name[, dictionary, context_instance,
  content_type, status, current_app, dirs])``
* ``render_to_response(template_name[, dictionary, context_instance,
  content_type, dirs])``

The new public APIs are:

* ``render(request, template_name[, context, using, content_type, status])``
* ``render_to_response(template_name[, context, using, content_type, status])``

``dictionary`` is renamed to ``context`` because it's a better name and
because it's consistent with template responses. This is transparent when it's
passed as a positional argument, which is the most common idiom. A deprecation
path is provided for when it's passed as a keyword argument.

``context_instance`` is deprecated in favor of ``context``. A compatibility
shim will allow passing a ``Context`` or a ``RequestContext`` in ``context``
during the deprecation period.

``using`` provides a way to select a template engine explicitly.

``render_to_response`` gains a ``status`` argument for consistency with
``render`` which gained it in 0fef92f6_.

``current_app`` is used by the ``{% url %}`` tag for reversing namespaced
URLs. Such coupling is embarrassing. It doesn't serve any other purpose. There
are two alternatives to hardcoding this feature in the template rendering API:
looking up ``current_app`` as an attribute of ``request`` or as a value in
``context``. The former makes more sense because the current application is
really a property of the request being handled and because ``current_app`` is
only supported by ``RequestContext``. For these reasons the ``current_app``
keyword argument of ``render`` is deprecated in favor of a ``current_app``
attribute of ``request``.

``dirs`` is new in Django 1.7 and deprecated without a replacement in Django
1.8. Only the Django Template Language will support it in Django 1.8 and 1.9.
It was added in 2f0566fa_ in order to fix `ticket #4278`_. Unfortunately that
ticket was very old and no longer made sense once template loaders were
introduced. Besides the current implementation doesn't even work: ``dirs``
doesn't apply to extended or included templates.

Template responses
------------------

The current public APIs are:

* ``TemplateResponse(request, template[, context, content_type, status,
  current_app, charset])``
* ``SimpleTemplateResponse(template[, context, content_type, status,
  charset])``

``current_app`` is treated exactly like for ``render``.

Public method ``resolve_context`` loses its purpose once ``Template.render``
no longer requires a ``Context`` and is deprecated.


Backwards Compatibility
=======================

All backwards-incompatible changes to public APIs will go through a
deprecation path according to Django's API stability policy. Notable changes
include:

- removing the ``TEMPLATE_*`` settings, except ``TEMPLATE_DEBUG``
- moving ``context_processors`` from ``django.core`` to ``django.template``
- turning ``current_app`` into an attribute of the ``request`` object
- changing the signature of ``render``, ``render_to_response`` and
  ``render_to_string``, although this won't affect the most common use case
- removing the ``dirs`` argument of template-finding functions
- moving the base class for template loaders

Since this project involves a large amount of refactoring, many private APIs
will change. In order to clarify the landscape, private APIs imported in the
``django.template`` namespace will be removed. Only public APIs will be left.
The author will make an effort to provide a deprecation path or document the
removal of private APIs that are likely to be used in the wild.


Reference Implementation
========================

In progress.


Appendix: the Django Template Language
======================================

Documentation
-------------

Django's documentation describes the Django Template Language in four pages:

* `Topic guide`_
* `Reference`_
* `Built-in tags and filters`_
* `Custom tags and filters`_

Features
--------

The syntax of the Django Template Language supports four constructs:

* Variables and lookups
* Filters, built-in or custom
* Tags, built-in or custom
* Comments

In addition, its rendering engine provides four notable features:

* Template inheritance
* Support for internationalization, localization and time zones
* Automatic HTML escaping for XSS protection
* Tight integration with the CSRF protection

It also provides debatable "designer-friendly" error handling.

Settings
--------

Currently Django provides six settings to configure its template engine:

* ``ALLOWED_INCLUDE_ROOTS`` is an artifact of the ``{% ssi %}`` tag which
  should be uncommon in modern Django projects.

* ``TEMPLATE_CONTEXT_PROCESSORS`` configures template context processors,
  which make common values available in the context of any template that is
  rendered with a ``RequestContext``.

* ``TEMPLATE_DEBUG`` is a generic switch. When it's set, Django creates a
  template stack trace when an exception occurs in a template and adds an
  ``origin`` attribute to ``Template`` objects. Since it doesn't appear useful
  to set in on a per-engine basis, it should remain a global setting.

* ``TEMPLATE_DIRS`` configures the filesystem template loader. It's superseded
  by the ``DIRS`` setting in each template backend.

* ``TEMPLATE_LOADERS`` configures templates loaders.

* ``TEMPLATE_STRING_IF_INVALID`` is a debugging tool that suffers from
  usability issues. It cannot be permanently set to a non-empty value because
  the admin misbehaves in that case. Everyone pretends that it doesn't exist.

Except for ``TEMPLATE_DEBUG``, all these settings should become options in the
configuration of Django template backends and lose their ``TEMPLATE_`` prefix.

The template engine also takes a few other settings into account:

* ``FILE_CHARSET`` defines the charset of template files loaded from the
  filesystem. Third-party template engines should honor its value.

* ``INSTALLED_APPS`` defines the content of the application registry, which is
  then used by the app directories template loaders to locate templates in
  installed applications.

* ``DATE_FORMAT``, ``SHORT_DATE_FORMAT`` and ``SHORT_DATETIME_FORMAT``
  describe formatting of dates and datetimes in templates when localization
  is disabled. Third-party template engines may use them if it makes sense.

* ``USE_I18N``, ``USE_L10N`` and ``USE_TZ`` activate internationalization,
  localization and time zones. Third-party template engines that provide
  comparable features should account for these settings.

Loaders
-------

Django ships four loaders, two of which are enabled by default:

* ``filesystem``: searches ``TEMPLATE_DIRS``
* ``app_directories``: searches the ``templates`` subdirectories of installed
  applications
* ``eggs``: like ``app_directories`` but for applications installed as eggs
* ``cached``: wraps other loaders and caches compiled templates

Loaders are invoked through global APIs: ``get_template`` and
``select_template``.

Custom loaders are implemented by subclassing ``BaseLoader`` and overriding
``load_template_source``.

The documentation describes how to return a non-DTL template from a loader.
While this is a reasonable point to interface with a third-party template
engine, the current API requires lots of glue code. That's why this proposal
offers a more structured solution.

Rendering
---------

In addition to the expected ``Template`` class, there are two ``Context``
classes:

* ``Template``: parses a string and compiles it, provides a ``render`` method
* ``Context``: like a ``dict``, except it's a stack of ``dict``, also stores
  some state used for rendering
* ``RequestContext``: like ``Context`` but runs template context processors

In order to preserve loose coupling, ``Context`` doesn't know anything about
HTTP requests. But almost all templates need values from the ``request``.
``RequestContext`` is the pragmatic answer: it's instantiated with ``request``
and passes it to context processors.

Built-in context processors are defined in ``django.core.context_processors``.
They were introduced in 49fd163a_ and b28e5e41_. At that time, the template
engine was implemented in ``django.core.template``. The magic-removal refactor
moved the template engine to ``django.template`` but didn't touch context
processors.

Context processors make various bits of Django easier to interact with in
templates. They don't quite belong to ``django.core``. In contrib apps, they
live at the top level, like middleware and template tags. The corresponding
location for Django context processors would be ``django.context_processors``,
next to ``django.templatetags``. However, since they're specific to the Django
Template Language, ``django.template.context_processors`` seems more natural.

The CSRF processor is hardcoded in ``RequestContext`` in order to remove one
configuration step and thus minimize the likelihood that users simply disable
the CSRF protection.

Shortcuts
---------

While it isn't part of the template engine itself, the ``django.shortcuts``
module provides the ``render`` function, which is the most common entry point
for rendering a template, and its sibling ``render_to_response``.

These functions invoke ``render_to_string`` to render the template and wrap
the result in a ``HttpResponse``.

``render`` creates a ``RequestContext`` for rendering while
``render_to_response`` uses a plain ``Context``.

Template responses
------------------

``SimpleTemplateResponse`` and ``TemplateResponse`` are bridges between
``HttpResponse`` and the template engine. While they're defined in
``django.template.response``, they cannot be considered as features of the
template engine.

``TemplateResponse`` creates a ``RequestContext`` for rendering while
``SimpleTemplateResponse`` uses a plain ``Context``.

Public APIs
-----------

Here's a summary of the template-related APIs mentioned in the `reference
documentation`_. It encompasses all APIs that interact with other components.
APIs for defining custom template tags and filters aren't included because
they're internal to the Django Template Language, thus irrelevant here. All
Python paths are relative to ``django.template``.

Template
~~~~~~~~

* ``Template(str)``
* ``Template.render(context)``
* ``Template.origin`` — when ``TEMPLATE_DEBUG`` is ``True``, it's either a
  ``loader.LoaderOrigin`` or a ``StringOrigin``

Context
~~~~~~~

* ``Context([dict, current_app])``
* ``Context.__getitem__(key)``
* ``Context.__setitem__(key, value)``
* ``Context.__delitem__(key)``
* ``Context.push(**context)`` — it works as a context manager too
* ``Context.pop()``
* ``Context.update(context)`` — like ``push(**context)``
* ``Context.flatten()``
* ``Context.dicts`` — it appears in the example of supporting an alternative
  template language

RequestContext
~~~~~~~~~~~~~~

* ``RequestContext(request, [dict, processors, current_app])``

loader
~~~~~~

* ``loader.get_template(template_name[, dirs])``
* ``loader.select_template(template_name_list[, dirs])``
* ``loader.render_to_string(template_name, [dictionary, context_instance])``

Exceptions
~~~~~~~~~~

* ``TemplateDoesNotExist``
* ``TemplateSyntaxError``

Conventional attributes
~~~~~~~~~~~~~~~~~~~~~~~

* Django won't call a callable variable:
    * If it has an ``alters_data`` attribute that evaluates to ``True``; it
      will render ``TEMPLATE_STRING_IF_INVALID`` instead.
    * If it has a ``do_not_call_in_templates`` attribute that evaluates to
      ``True``; it will render the string representation of the callable.
* If resolving a callable variable triggers an exception and that exception
  has a ``silent_variable_failure`` attribute that evaluates to ``True``,
  Django will swallow the exception and render ``TEMPLATE_STRING_IF_INVALID``.

Private APIs
------------

The following APIs aren't documented but will have to be made public to allow
for feature parity between the Django Template Language and third-party
template engines.

Debug
~~~~~

* ``Origin.reload()``
* If an exception has a ``django_template_source`` attribute, it's expected to
  be in the format ``origin, (start, end)`` where ``origin`` is an ``Origin``
  instance and ``start, end`` provide the location of the error in that file.

Dependency analysis
-------------------

This section reviews dependencies on ``django.template`` or
``django.templatetags`` from other components of Django and singles out
reliance on private APIs.

The list of dependencies was built by searching for ``from django import
template`` and ``from django.template`` in the source tree.

Public APIs
~~~~~~~~~~~

Various parts of Django depend on the public APIs of ``Template``,
``Context``, ``RequestContext``, and ``loader``.

Contrib apps that provide views often import ``SimpleTemplateResponse`` or
``TemplateResponse``.

Template tags and filters libraries in core and in contrib apps instantiate a
``Library``.

Private APIs
~~~~~~~~~~~~

``django.test.signals`` depends on various internals of the template engine to
reset their state when the corresponding settings change.

``django.test.utils`` defines two context managers and decorators,
``override_template_loaders`` and ``override_with_test_loader``, that are used
by the template tests and a few others.

``django.utils.translation.templatize`` invokes the lexer of the template
engine to extract tokens and generate a pseudo-Python file that ``xgettext``
can parse.

``django.views.debug`` relies on some internals of the template loading
infrastructure.

The admindocs contrib app depends on internals of the Django Template Language
to introspect template tags and filters libraries.

``test_client_regress.tests.TemplateExceptionTests`` resets internals of the
template loading infrastructure.

Template filters
~~~~~~~~~~~~~~~~

``django.views.debug`` imports directly the ``force_escape`` and ``pprint``
template filters.

``django.contrib.admin.helpers`` imports directly the ``capfirst`` and
``linebreaksbr`` template filters.

``django.contrib.humanize.templatetags.humanize`` imports directly the
``date``, ``floatformat``, ``timesince``, and ``timeuntil`` template filters.


Appendix: extraction of translatable strings
============================================

Currently the ``makemessages`` management command is implement as follows.

* It walks the filesystem under the current working directory (``.``).
* It builds a list of files to process and corresponding locale paths.
* It extracts translatable strings from each file with ``xgettext``:
    * If the domain is ``django``:
        * If the file extension is ``.py``, the file is processed by
          ``xgettext`` as is.
        * If it's another known extension — ``.html`` and ``.txt`` by default,
          or the values set on the command line — the file is assumed to be a
          Django template and is run through a 200-line function that spits a
          syntactically correct Python file with the appropriate translation
          calls at the same line numbers. The resulting file is processed by
          ``xgettext``.
        * Otherwise, the file ignored.
    * If the domain is ``djangojs``:
        * If the file extension is known — ``.js`` by default, or the values
          set on the command line — the file is transformed into something
          that resembles C. The resulting file is processed by ``xgettext``.
        * Otherwise, the file ignored.
* The output of ``xgettext`` is appended to a ``.pot`` file in the target
  locale directory with minor adjustments.
* Message catalogs ie. ``.po`` files for each language are updated according
  to the ``.pot`` file with ``msgmerge``.


Appendix: Python template engines
=================================

This section shows basic usage of common Python template engines in a web
application.

All examples except Django follow the configure / load / render lifecycle.

Template engine adapters for Django would wrap these APIs.

Examples render a template called ``NAME = 'hello.html'`` found in one of
``TEMPLATE_DIRS`` with a context defined as ``CONTEXT = {'name': 'world'}``.

Chameleon_
----------

.. code:: python

    from chameleon import PageTemplateLoader

    loader = PageTemplateLoader(TEMPLATE_DIRS)
    template = loader[NAME]
    html = template.render(**CONTEXT)

Configuration is performed by passing keyword arguments to
``PageTemplateLoader``, which passes them to ``render``.

Django_
-------

.. code:: python

    from django.template import loader

    template = loader.get_template(NAME)
    html = template.render(CONTEXT)

or:

.. code:: python

    from django.template.loader import render_to_string

    html = render_to_string(NAME, CONTEXT)

or:

.. code:: python

    from django.template.loader import render_to_string

    # assuming the code is handling a HttpRequest
    html = render_to_string(NAME, CONTEXT, RequestContext(request))

Configuration is performed through global settings. (This is bad.)

Genshi_
-------

.. code:: python

    from genshi.template import TemplateLoader

    loader = TemplateLoader(TEMPLATE_DIRS)
    template = loader.load(NAME)
    html = template.generate(**CONTEXT).render('html')

The author couldn't determine how configuration is performed. Genshi is more
complex than other engines analyzed here.

Jinja2_
-------

.. code:: python

    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIRS))
    template = env.get_template(NAME)
    html = template.render(**CONTEXT)

Jinja2 has a concept of environment that contains global configuration.
Template loading is exposed as a method of the environment.

Loaders are configured in the environment. Jinja2 provides roughly the same
loaders as Django.


Mako_
-----

.. code:: python

    from mako.lookup import TemplateLookup

    lookup = TemplateLookup(TEMPLATE_DIRS)
    template = lookup.get_template(NAME)
    html = template.render(**CONTEXT)

Configuration is performed by passing keyword arguments to ``TemplateLookup``,
which passes them to ``render``.

`Template strings`_
-------------------

Template strings provide simplified string interpolation. They only implement
rendering, with a variant that raises exceptions for missing substitutions and
another variant that ignores them.

.. code:: python

    from string import Template

    html = Template("Hello $name").safe_substitute(**CONTEXT)


Appendix: Django - Jinja2 adapters
==================================

There are three maintained and mature Django - Jinja2 adapters: in
chronological order, Coffin, Jingo, and Django-Jinja.

Coffin
------

Coffin provides replacements for several Django APIs related to templates such
as ``render``. Views must use Coffin APIs explicitly.

This approach predates 44b9076b_ which recommends integrating third-party
template engines with custom template loaders.

Coffin focuses on minimizing differences between Django and Jinja2 template by
making many Django filters and tags usable from Jinja2 templates.

Jingo
-----

Jingo provides a template loader for Jinja2 templates that must be placed
before Django's template loaders in ``TEMPLATE_LOADERS``.

It provides APIs for registering globals and filters, but not tests. It
recommends doing the registration in a conventional ``helpers`` submodule in
installed applications.

It registers a few globals and filters, including replacements for two of
Django's most useful template tags: ``csrf`` and ``url``. However it doesn't
deal with ``static``.

It's capable of monkey-patching support for ``__html__`` but that isn't needed
any more since af64429b_.

Django-Jinja
------------

Django-Jinja replaces Django's template loaders with alternatives that handle
both Jinja2 and the DTL.

It advertises wide compatibility with Django template filters and tags. The
documentation doesn't talk about limitations, if any.

It integrates with Django's i18n framework, especially the ``makemessages``
management command.

It connects Jinja2's bytecode cache to Django's caching framework.

It provides APIs for registering globals and filters.

It includes ``url`` and ``static`` globals to replace Django's tags.

It supports a few popular third-party applications explicitly.


FAQ
===

Why not simply switch to Jinja2?
--------------------------------

Since the Django Template Language shares some syntax with Jinja2, it's
possible to write a trivial example that will work with both engines.

However, as shown above, the DTL provide several features that don't have a
straightforward equivalent in Jinja2.

Porting a non-trivial application from the DTL to Jinja2 requires a
significant amount of work and cannot be automated.

If you aren't convinced, try porting the ``django.contrib.admin`` templates —
barely 1200 lines of template code — and see for yourself.

Shouldn't Jinja2 be the default?
--------------------------------

In order to minimize disruption for developers, this project doesn't change
the default engine. However it paves the way for doing so in a later release.

Will the Django Template Language be deprecated?
------------------------------------------------

No, there is no plan to deprecate it at this time.

How does this account for differences in APIs?
----------------------------------------------

As shown above, most Python template engines support the following pattern:

.. code:: python

    loader = TemplateLoader(**CONFIG)
    template = loader.load(NAME)
    html = template.render(**CONTEXT)

This basic API serves as a common denominator for all engines. Then each
engine may expose additional features through ``TemplateLoader`` options.

Isn't this going to fragment the ecosystem of pluggable apps?
-------------------------------------------------------------

First, there's a debate about the usefulness of shipping user-facing templates
in pluggable apps. Templates must be customized to fit the website's design,
usually by inheriting a base template. That's why many pluggable apps don't
ship templates and document which templates the developer must create instead.
In that case, the developer can use their favorite template engine.

If a pluggable app ships standalone templates, then which template engine
they're written for doesn't matter. The author must document which template
engine it uses and the developer must ensure their project meets this
requirement.

Pluggable apps that provide DTL filters or tags are strongly encouraged to
provide equivalent Python functions in their public APIs for interoperability
with all template engines. The DTL filters or tags should be thin wrappers
around the plain Python functions.

Is it possible to use Django template filters or tags with other engines?
-------------------------------------------------------------------------

This project doesn't aim at creating Django-flavored versions of various
Python template engines. It aims at building a foundation upon which every
developer can create the template engine they need if it doesn't exist yet.

In other words this idea may be implemented but it belongs to a third-party
module.

What about template loaders and context processors?
---------------------------------------------------

Likewise, these are specific features of the DTL. Other engines should provide
their own APIs for loading templates and for adding common context to all
templates.

Can Django support my favorite JavaScript template engine?
----------------------------------------------------------

Nice try ;-) This is out of scope for this project.


Acknowledgments
===============

Thanks Collin Anderson, Loic Bistuer, Tim Graham, Jannis Leidel, Carl Meyer,
Michael Manfre, Baptiste Mispelon, Daniele Procida, Josh Smeaton, and Marc
Tamlyn for commenting drafts of this document. Many good ideas are theirs.


Copyright
=========

This document has been placed in the public domain per the `Creative Commons
CC0 1.0 Universal license`_.


.. _Jinja2: http://jinja.pocoo.org/
.. _quite opinionated: https://docs.djangoproject.com/en/1.7/misc/design-philosophies/#template-system
.. _have failed: https://github.com/mitsuhiko/templatetk/blob/master/POST_MORTEM
.. _simple_tag: https://docs.djangoproject.com/en/1.7/howto/custom-template-tags/#simple-tags
.. _inclusion_tag: https://docs.djangoproject.com/en/1.7/howto/custom-template-tags/#inclusion-tags
.. _assignment_tag: https://docs.djangoproject.com/en/1.7/howto/custom-template-tags/#assignment-tags
.. _template-based widget rendering: https://code.djangoproject.com/ticket/15667
.. _loose coupling: https://docs.djangoproject.com/en/1.7/misc/design-philosophies/#loose-coupling
.. _half a dozen libraries: https://www.djangopackages.com/grids/g/jinja2-template-loaders/
.. _template strings: https://docs.python.org/3/library/string.html#template-strings
.. _Babel: http://babel.pocoo.org/
.. _49fd163a: https://github.com/django/django/commit/49fd163a95074c07a23f2ccf9e23aebf5bee0bb2
.. _b28e5e41: https://github.com/django/django/commit/b28e5e413332ac2becb9f475367783b94db889fc
.. _Chameleon: https://chameleon.readthedocs.org/
.. _Django: https://docs.djangoproject.com/en/1.7/topics/templates/
.. _Genshi: http://genshi.edgewall.org/
.. _Mako: http://docs.makotemplates.org/
.. _44b9076b: https://github.com/django/django/commit/44b9076bbed3e629230d9b77a8765e4c906036d1
.. _af64429b: https://github.com/django/django/commit/af64429b991471b7a441e133b5b7d29070984f24
.. _0fef92f6: https://github.com/django/django/commit/0fef92f6f0d064cdce4e8722fd9fe27ed451bb9b
.. _2f0566fa: https://github.com/django/django/commit/2f0566fa61e13277364e3aef338fa5c143f5a704
.. _ticket #4278: https://code.djangoproject.com/ticket/4278
.. _932d449f: https://github.com/django/django/commit/932d449f001a94aa5065cda652a442e4b1dd5352
.. _Topic guide: https://docs.djangoproject.com/en/1.7/topics/templates/
.. _Reference: https://docs.djangoproject.com/en/1.7/ref/templates/api/
.. _Built-in tags and filters: https://docs.djangoproject.com/en/1.7/ref/templates/builtins/
.. _Custom tags and filters: https://docs.djangoproject.com/en/1.7/howto/custom-template-tags/
.. _reference documentation: https://docs.djangoproject.com/en/1.7/ref/templates/api/
.. _Creative Commons CC0 1.0 Universal license: http://creativecommons.org/publicdomain/zero/1.0/deed
