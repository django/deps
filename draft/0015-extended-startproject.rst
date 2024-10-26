======================================
DEP 15: Extended startproject template
======================================

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
app by default.

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

To get a working app, it's then necessary to run ``startapp``, which results in:

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

The current tutorial could then be updated to use this new structure.

Motivation
==========

New users often struggle to get off the ground when following the tutorial.
Two known sticking points are:

- Confusion around having multiple folders.
- Confusion around having two ``urls.py`` files.

It is also expected that by removing a step, the tutorial will be easier and
faster to follow. This also has implications for improving other unofficial
tutorials such as the Django Girls tutorial used in their workshops.

Rationale
=========

Another way to do this could be to modify the existing template. However, this
would cause some disruption to the community. Some people like the existing
template, and third party tutorials such as Django Girls would need to be
updated.

The proposed solution also has drawbacks however, in that there will be
duplication between the two templates. To mitigate this, the existing template
could be deprecated over some time period.

Another benefit of this solution is that it will set a precedent for adding new
templates into Django. This could be useful for other templates such as a
single file project for quick prototyping.

Relevant discussions
--------------------

- `Django New Project Structure/Name <https://forum.djangoproject.com/t/django-new-project-structure-name/9987>`_
- `Updating the default startapp template <https://forum.djangoproject.com/t/updating-the-default-startapp-template/24193>`_
- `Update startproject with default login/signup/logout options <https://forum.djangoproject.com/t/update-startproject-with-default-login-signup-logout-options/35175>`_
- `The Single Folder Django Project Layout <https://noumenal.es/notes/django/single-folder-layout/>`_

Reference Implementation
========================

TODO.

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).
