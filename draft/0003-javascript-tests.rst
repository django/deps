================
JavaScript Tests
================

:DEP: 0003
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

`Jasmine`_ is a `BDD`_ testing frameworks similar to Ruby's `RSpec`_.
`QUnit`_ is a testing framework that uses a declarative testing style akin to
Django's existing testing framework.  `Mocha`_ is a BDD testing framework that
can also be used in a more declarative style with a syntax very similar to
QUnit's.

QUnit should be used because it is:

- Popular (used by `jQuery`_, `Backbone.js`_, and `Ember.js`_)
- Similar to the Python test suite (it is not a BDD framework like Jasmine)
- Easy to setup (like Jasmine and Mocha, it only requires a JS and HTML file)
- QUnit auto-resets the ``#qunit-fixture`` element which allows for more certain
  test isolation

Blanket for code coverage
-------------------------

`Istanbul`_ and `Blanket.js`_ are both popular JavaScript code coverage tools.
Using Istanbul in a web browser requires using a Node.js command-line tool to
generate Istanbul-wrapped test files.  Blanket.js can inject itself into your
code directly from a web browser and therefore does not require generating new
test files.

Blanket.js should be used so that code coverage can be may be verified in a
web browser without requiring Node.js.

Migration Path
--------------

The proposed migration path:

1. Add a ``package.json`` file and a ``Gruntfile.js`` and introduce
   command-line `QUnit`_ tests with `Blanket.js`_ for code coverage
2. Add a few easy-to-implement tests to start (low-hanging fruit)
3. Add JSHint and update code to conform to a style dictated in a ``.jshintrc``
   file
4. Add EditorConfig for auto-enforced code style guide (needed for mixed
   indentation)
5. Document process used to run the tests from the command line and within a
   browser
6. Setup CI server to run the tests

Running tests in a web browser should be as easy as either:

1. Opening ``./js_tests/tests.html`` in your web browser (ideal case)
2. Executing ``python -m SimpleHTTPServer`` and opening
   http://localhost:8000/js_tests/tests.html in your web browser

Running tests from the command-line (locally or on the CI server) should be as
easy as:

1. Install `Node.js`_
2. Run ``npm install`` to install all local Node dependencies
3. Run ``npm test`` to run the tests and read the results

Open Questions
--------------

- How should the test framework be run within the CI process?
- How should the testing documentation be updated for the new JavaScript test
  framework?


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


Reference Implementation
========================

Pull request `#4573 <https://github.com/django/django/pull/4573>`_ implements
all suggested changes in this DEP.


Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license
(http://creativecommons.org/publicdomain/zero/1.0/deed).

.. _backbone.js: http://backbonejs.org/
.. _blanket.js: http://blanketjs.org/
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
