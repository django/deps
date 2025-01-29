========================================
DEP XXXX: Name the main command `django`
========================================

:DEP: XXXX
:Author: Ryan Hiebert
:Implementation Team: Ryan Hiebert
:Shepherd: Tom Carrick
:Status: Draft
:Type: Feature
:Created: 2025-01-07

.. contents:: Table of Contents
   :depth: 3
   :local:


Abstract
========

Motivated by a desire to remove confusing papercuts in Django
and to follow common convention in the Python ecosystem,
this DEP proposes to add a new ``django`` command equivalent to
the existing ``django-admin`` command,
and to update the documentation to prefer this new spelling.

Specification
=============

The ``django`` command will be added as the preferred spelling
for the existing ``django-admin`` command.
The ``django-admin`` command will remain indefinitely,
with a message that says

  The ``django-admin`` command is being renamed to ``django``.
  You can keep using either name,
  they are equivalent except for the printing of this message.
  For more details on the naming change, see DEP XXXX.

Official documentation will be updated
to reference this new ``django`` command
everywhere that ``django-admin`` is currently referenced.
The implementor will coordinate with the translation team
to assist in making all necessary translation updates.

Backwards Compatibility
=======================

The existing ``django-admin`` command will remain indefinitely
as an alias of the ``django`` command,
with messaging about the new name.
There are no plans to remove the ``django-admin`` alias.

Motivation
==========

Django is how many people first learn Python,
so the choices that Django makes have an outsized impact
on the intuition they have of how things work in Python.
This makes it more important that Django
follow Python's simple and clean style,
and match the conventions of the broader ecosystem.

Naming the main command ``django``
can reduce new developer confusion and make it easier to remember
by following the most typical patterns in both the Python ecosystem
and in the broader software development world.
Some Python examples include ``pip``, ``pytest``, and ``black``,
and some broader examples include ``ember``, ``rails``, and ``vite``.

The broad acceptance of this pattern has been reinforced
by tools like ``uv tool run`` (aka ``uvx``) and ``pipx``,
where commands that are the same as the package name
get special privileges and a simpler syntax.
For example ``uvx pytest`` automatically downloads and runs
the ``pytest`` command from the ``pytest`` package.

This pattern has been further reinforced
by the common pattern of recommending to use, for example,
``python -m pip`` to ensure that
you're using the version of the module
that is associated with your intended Python interpreter.
The correspondance between the command name and the package name
allows for a more intuitive mapping to the alternative style.

The ``django`` command is shorter,
and while tab completion is a common way to avoid typing long commmands
not all developers use it,
especially new developers who are still learning
how the command line works.
Mentors in Django Girls workshops have observed that
people have trouble remembering that they can use tab completion.

Some commenters have described this alternative as
intuitive, fun, aesthetic, and modern.
These subjective benefits
are not sufficient motivation to make the change alone,
and are likely to be largely based on the intuitions built
from the motivations above,
but they reinforce values that we desire in the project.

Drawbacks
=========

All changes have some drawbacks, this is no exception.
It is important to consider them,
and to make sure that they are mitigated
or are outweighed by the benefits,
compared with the implied work of
reviewing and assuring the quality of the change,
which will fall to the fellows and community reviewers.

Broad community effects
-----------------------

There are many existing tutorials and blog posts
that reference the existing ``django-admin`` commmand,
and authors may reasonably think it wisest to update them.
This is work that will be done by the community,
so we should be cautious with adding this burden.

Because the existing command will remain,
the benefits of having the command follow common conventions
and build the right mental model for new developers outweigh the cost.

More than one way to do it
--------------------------

Having multiple ways to spell the same thing can be confusing
by making it difficult for users to know which is the correct way,
and worry what differences there are between them.
This concern is especially relevant because of the volume
of external resources that reference the existing command name.

This drawback is mitigated by clear documentation
that the two commands are equivalent,
the added messaging in the ``django-admin`` command,
and because the benefits of
following common convention outweigh the cost.

Ambiguity
---------

The ``django`` command can be seen as a terminology conflict
with the name of the Python package or the name of the project itself.
However, this name overlap is an important feature.

Django is an exception to what most tools with a CLI do,
so the current situation is already confusing to new users.
It is worth the trade of some confusion over this ambiguity
for the clarity gained by consistency with other tools.
Over time, usage of the current command will be less common,
and the confusion will be less likely to surface.

Additionally, the existing also ``django-admin`` command name
has a conceptual conflict with the Django Admin,
the CRUD admin interface
that Django enables for new project by default.

Alternatives
============

Beside the status quo, some other possibilities compete with this proposal.

Only add an alias
-----------------

This could be a less invasive change by only adding the new command name,
and not modifying the documentation
or printing a message in the ``django-admin`` command.
This would avoid the vast majority of the work involved in this change.
However, some common challenges are caused
by the command name being different from the package name,
and won't be resolved until the documentation is updated as well.
For example, users have tried to run
``python -m django-admin`` instead of ``python -m django``,
to mirror the pattern followed by
other notable Python packages with commands.

.. code-block:: bash

   python -m django-admin startproject myproject

``django-admin`` is not a valid Python module name,
so this command cannot be run in this way.

Reserve the name
----------------

``django-admin`` is only commonly used directly to create new projects,
with ``django-admin startproject``,
so it is reasonable to wonder whether matching ``django-admin``
is the optimal behavior for this name.

One other interesting candidate for the ``django`` command has been suggested,
which is to use it as a replacement for the generated ``manage.py`` script.
Because the ``manage.py`` script is effectively
a wrapper around the same code as ``django-admin``,
``manage.py`` is a strict superset of ``django-admin``.
This means that the ``django`` command could be expanded
to be a replacement for ``manage.py`` in the future.

Reference Implementation
========================

Two separate proof of concept implementations were written
by `Jeff Triplett`_ and `Ryan Hiebert`_.

.. _Jeff Triplett: https://github.com/jefftriplett/django-cli-no-admin
.. _Ryan Hiebert: https://github.com/ryanhiebert/django-cmd

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).

(All DEPs must include this exact copyright statement.)
