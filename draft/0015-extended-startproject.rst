=======================================
DEP 15: Improved startproject interface
=======================================

:DEP: 15
:Author: Tom Carrick
:Implementation Team: Tom Carrick
:Shepherd: Carlton Gibson
:Status: Draft
:Type: Feature
:Created: 2024-10-26
:Last-Modified: 2024-10-26

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

The current method of starting a new Django project involves running the
``startproject`` and ``startapp`` commands, which creates a project with
multiple folders. This structure can be confusing to new users. This DEP
proposes a new structure for the ``startproject`` command that includes an
app by default. Additionally, a new command will be added to provide a
multiple choice interface for setting up a new project using various
useful templates.

Further, documentation improvements will be made to use this new structure
and explain how to create new apps within the project.

Specification
=============

Currently, the ``startproject`` command creates a project with the following
structure:

.. code-block::

   .
   ├── manage.py
   └── myproject
      ├── __init__.py
      ├── asgi.py
      ├── settings.py
      ├── urls.py
      └── wsgi.py

To get a working app, it's then necessary to run ``startapp``, which results
in:

.. code-block::

   .
   ├── manage.py
   ├── myapp
   │   ├── __init__.py
   │   ├── admin.py
   │   ├── apps.py
   │   ├── migrations
   │   │   └── __init__.py
   │   ├── models.py
   │   ├── tests.py
   │   └── views.py
   └── myproject
      ├── __init__.py
      ├── asgi.py
      ├── settings.py
      ├── urls.py
      └── wsgi.py


This DEP proposes that Django should include a template to be able to create a
project with an app pre-installed. The new structure would look like this:

.. code-block::

   .
   ├── manage.py
   └── myproject
      ├── __init__.py
      ├── admin.py
      ├── apps.py
      ├── asgi.py
      ├── migrations
      │   └── __init__.py
      ├── models.py
      ├── settings.py
      ├── tests.py
      ├── urls.py
      ├── views.py
      └── wsgi.py

The ``settings.py`` file will be updated to include the project directory in
``INSTALLED_APPS``.

A new command called ``new`` will be added to provide a user friendly interface
for setting up a new project. This command may be a frontend of startproject.

The current tutorial could then be updated to use this new command and
structure.

The initial templates proposed are:
1. The structure above, with a single app. This will be the default for the
  ``new`` command, but not for ``startproject`` for backwards compatibility.
2. A minimal single file project for quick prototyping and testing. This might
  be especially useful for contributors.
3. A template suitable for writing a third party app.
4. A "classic" project structure using the current ``startproject`` template.

A URL can also be entered that works the same way as ``startproject``.

If ``--noinput`` is passed to the command, it will select the default template.

This command could be extended later either by contributions to Django or perhaps
by third party packages.

Motivation
==========

This proposal helps solve multiple problems currently encountered by Django
users.

New user experience
-------------------

New users often struggle to get off the ground when following the tutorial.
Two known sticking points are:

* Confusion around having multiple folders.
* Confusion around having two ``urls.py`` files.

It is also expected that by removing a step, the tutorial will be easier and
faster to follow. This also has implications for improving other unofficial
tutorials such as the Django Girls tutorial used in their workshops.

Contributors
------------

Contributors often need to set up a new project to test their changes. It's
not really documented anywhere how to do this, so there is no standard process.
This can be a barrier to entry for new contributors. Examples of current
methods include:

1. Using a project using models from the test suite.
2. The user maintains their own test project that expands over time.
3. Spinning up a fresh project each time.
4. Using a ready built site such as ``django-admind-demo``.
5. Using one of the various single file templates from the web.

Of these, this proposal makes 3 and 4 easier, and 5 unnecessary as the default
structure will be faster to spin up and get working with, and the single file
project will always work with the current branch.

Third party apps
----------------

Setting up a third party app can be quite complex. Something as simple as
running tests or the ``makemigrations`` command can be quite tricky to figure
out.

Developers
----------

Developers also benefit from this proposal as they get to a working state
faster. They are still free to choose any layout they prefer, but by
modernizing the default template it is hoped that projects will become more
consistent and easier for people to find their way around.

Rationale
=========

Another way to do this could be to modify the existing template. However, this
would cause some disruption to the community. Some people like the existing
template, and third party tutorials such as Django Girls would need to be
updated.

Simply adding a new template without a new command was also considered, but
this makes it more difficult for people to find and use the new template. It
also allows us to create a new default template, while still using the old
template for ``startproject`` for backwards compatibility.

Another benefit of this solution is that it will set a precedent for adding new
templates into Django. This could be useful for other templates such as a
more complete setup for a REST API, or a project with useful frontend
components. This would allow Django to have a supported and suggested way to
integrate a frontend framework without being tied to a single framework.
However there are a lot of risks involved with this, so it is not proposed
here.

Relevant discussions
====================

* `Django New Project Structure/Name <https://forum.djangoproject.com/t/django-new-project-structure-name/9987>`_
* `Updating the default startapp template <https://forum.djangoproject.com/t/updating-the-default-startapp-template/24193>`_
* `Update startproject with default login/signup/logout options <https://forum.djangoproject.com/t/update-startproject-with-default-login-signup-logout-options/35175>`_
* `The Single Folder Django Project Layout <https://noumenal.es/notes/django/single-folder-layout/>`_

Reference Implementation
========================

TODO.

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).
