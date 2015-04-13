================
JavaScript Tests
================

:DEP: XXXX
:Author: Trey Hunner
:Implementation Team: Trey Hunner
:Shepherd: Carl Meyer
:Status: Draft
:Type: Process
:Created: 2014-05-04
:Last-Modified: 2015-04-13

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

Create unit tests for the JavaScript code in the admin and gis contrib packages.


Specification
=============

QUnit test framework
--------------------

`Jasmine`_ and `Mocha`_ are `BDD`_ testing frameworks similar to Ruby's `RSpec`_
whereas `QUnit`_ uses a declarative testing style akin to Django's existing
testing framework.

QUnit should be used because it is:

- Popular (used by `jQuery`_, `Backbone.js`_, and `Ember.js`_)
- Similar to the Python test suite (it is not a BDD framework)
- Easy to setup (like Jasmine and Mocha, it only requires a JS and HTML file)

Migration Path
--------------

The proposed migration path:

1. Add a ``package.json`` file and a ``gulpfile.js`` and introduce
   command-line `QUnit`_ tests with `Istanbul`_ for code coverage
2. Add a few easy-to-implement tests to start (low-hanging fruit)
3. Add JSHint and update code to conform to a style dictated in a ``.jshintrc`` file
4. Document process used to run the tests from the command line and within a browser
5. Setup CI server to run the tests

Open Questions
--------------

- What steps should be taken to create the new JavaScript test framework?
- What tests should be created initially?
- How should the test framework be run within the CI process?
- How should the testing documentation be updated for the new JavaScript test framework?


Motivation
==========

Django ``admin`` and ``gis`` contrib packages contain JavaScript code without
any unit tests.  Django has functional tests which execute some of the
JavaScript code, but functional tests are not good enough.  Not all JavaScript
code can be tested without forcing the execution of low-level browser events.


Rationale
=========

Native JavaScript Testing Framework
-----------------------------------

A native JavaScript test framework is one that can be run without any Python
code, either in the browser or from the command line.

The JavaScript code can be tested independently of the Python code.  Therefore,
the JavaScript and Python tests do not need to be intertwined.

Arguments for
~~~~~~~~~~~~~

- Easier for a developer new to Django's JavaScript testing practices
- Tests can be run manually from a web browser without any need for `Node.js`_
- Creating tests only requires updating/creating a JavaScript file (no need to
  alter a py file)

Arguments against
~~~~~~~~~~~~~~~~~

- Executing automated tests on a continuous integration server without a Python
  wrapper will require `Node.js`_ and `PhantomJS`_
- JavaScript tests must be executed separately from Python tests
  (``./runtests.py`` will only execute Python tests)

The requirement of Node.js should not prove burdensome because:

- Running JS tests locally only requires opening an HTML file in a web browser
  (see `QUnit demo`_).
- `JSHint`_ (a popular JS linter) also requires Node.js and therefore Node.js
  may already be installed locally


Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).

.. _backbone.js: http://backbonejs.org/
.. _bdd: https://en.wikipedia.org/wiki/Behavior-driven_development
.. _ember.js: http://emberjs.com/
.. _istanbul: http://gotwarlost.github.io/istanbul/
.. _jasmine: http://jasmine.github.io/
.. _jshint: http://www.jshint.com/
.. _jquery: https://jquery.com/
.. _mocha: http://visionmedia.github.io/mocha/
.. _node.js: http://nodejs.org/
.. _phantomjs: http://phantomjs.org/
.. _qunit: https://qunitjs.com/
.. _qunit demo: http://jsfiddle.net/treyh/7kKG5/
.. _rspec: http://rspec.info/
