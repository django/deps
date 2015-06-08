==========================
JavaScript Tests & Linting
==========================

:DEP: 0003
:Author: Trey Hunner
:Implementation Team: Trey Hunner
:Shepherd: Carl Meyer
:Status: Draft
:Type: Process
:Created: 2014-05-04
:Last-Modified: 2015-06-08

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

Add unit tests and coding style consistency enforcement (linting) for the
JavaScript code in the admin and gis contrib packages.


Specification
=============

QUnit test framework
--------------------

`Jasmine`_ is a `BDD`_ testing frameworks similar to Ruby's `RSpec`_.  `QUnit`_
is a testing framework that uses a testing syntax similar to Django's existing
testing framework.  `Mocha`_ is a testing framework with pluggable testing
syntax options.

Any of these (especially QUnit or Mocha) could be a fine choice for
Django. This DEP selects QUnit because it is:

- Popular enough to provide some assurance of future maintenance (used by
  `jQuery`_, `Backbone.js`_, and `Ember.js`_).
- Similar syntax to the Python test suite (module/test/assert rather than
  describe/it/expect/should).
- Easy to setup (like Jasmine and Mocha, it only requires a JS and HTML file).
- Auto-resets the ``#qunit-fixture`` element, providing easy isolation for
  DOM-related tests (and much of Django's JS code is DOM-related).

Blanket for code coverage
-------------------------

`Istanbul`_ and `Blanket.js`_ are both popular JavaScript code coverage tools.
Using Istanbul in a web browser requires using a Node.js command-line tool to
generate Istanbul-wrapped test files.  Blanket.js can inject itself into your
code directly from a web browser and therefore does not require generating new
test files.

Blanket.js should be used so that code coverage can be verified in a web
browser without requiring Node.js.

EditorConfig for code style
---------------------------

The JavaScript files currently use a variety of code styles.  As an example,
some files use tabs for indentation, some use 4 spaces, and some use 2 spaces.
Fortunately, each file is fairly self-consistent.  Unfortunately, this variety
of styles makes manual code style enforcement difficult.

`EditorConfig`_ should be used to document the desired code style and maintain
this style while editing code.

JSHint for code linting
-----------------------

Linting code is particularly important in JavaScript due to certain hazardous
language features.  `JSHint`_ is a popular JavaScript linter which is based on
the less-customizable `JSLint`_ tool.  `ESLint`_ is a very customizable and
unopinionated JavaScript linter which also includes code style checking.

JSHint should be used initially because:

- It is customizable (unlike JSLint).
- It defaults to a good set of community standards.
- It does not enforce code style (style is not yet consistent between files).
- It is currently more widely used than JSLint or ESLint.

ESLint may be included later for stricter and more customizable linting and
code style enforcement after a future JavaScript code refactor.

Migration Path
--------------

The proposed migration path:

1. Add a ``package.json`` file and a ``Gruntfile.js`` and introduce
   command-line `QUnit`_ tests with `Blanket.js`_ for code coverage.
2. Add a few easy-to-implement tests to start (low-hanging fruit).
3. Add JSHint and update code to conform to a style dictated in a ``.jshintrc``
   file.
4. Add `EditorConfig`_ for auto-enforced code style guide.
5. Document process used to run the tests from the command line and within a
   browser.
6. Setup CI server to run the tests.

Running tests in a web browser is as easy as either:

1. Opening ``./js_tests/tests.html`` in your web browser (simplest case).
2. Executing ``python -m SimpleHTTPServer`` and opening
   http://localhost:8000/js_tests/tests.html in your web browser (needed for
   code coverage reporting).

Running tests via HTTP is required to run Blanket.js in the browser due to
`cross-origin resource sharing`_ rules.

Steps to run tests from the command-line (locally or on the CI server):

1. Install `Node.js`_.
2. Run ``npm install`` to install Node dependencies.
3. Run ``npm test`` to run the tests and see results, including code coverage.


Motivation
==========

Django ``admin`` and ``gis`` contrib packages contain JavaScript code without
any unit tests.  Django has functional tests which execute some of the
JavaScript code, but functional tests are not good enough.  Not all JavaScript
code can be tested without forcing the execution of low-level browser events.


Rationale
=========

A native JavaScript test framework is one that can be run without any Python
code, either in the browser or from the command line.

The JavaScript code can be tested independently of the Python code.  Therefore,
the JavaScript and Python tests do not need to be intertwined.

Arguments for
-------------

- Easier for a developer new to Django's JavaScript testing practices.
- Tests can be run manually from a web browser without any need for `Node.js`_.
- Creating tests only requires updating/creating a JavaScript file and updating
  an HTML file (no need to alter a py file).
- The JS community maintains a reliable set of testing tools.  Creating custom
  tools would require maintenance which no one has volunteered to do.

Arguments against
-----------------

- Executing automated tests on a continuous integration server without a Python
  wrapper will require `Node.js`_ and `PhantomJS`_.
- JavaScript tests must be executed separately from Python tests
  (``./runtests.py`` will only execute Python tests).

The requirement of Node.js should not prove burdensome because:

- Running JS tests locally only requires opening an HTML file in a web browser.
- `JSHint`_ (a popular JS linter) also requires Node.js and therefore Node.js
  may already be installed locally.


Reference Implementation
========================

Pull requests `#4573 <https://github.com/django/django/pull/4573>`_ and `#4577
<https://github.com/django/django/pull/4577>`_ implement all suggested changes
in this DEP.


Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).

.. _backbone.js: http://backbonejs.org/
.. _blanket.js: http://blanketjs.org/
.. _bdd: https://en.wikipedia.org/wiki/Behavior-driven_development
.. _cross-origin resource sharing: https://en.wikipedia.org/wiki/Cross-origin_resource_sharing
.. _editorconfig: http://editorconfig.org/
.. _ember.js: http://emberjs.com/
.. _eslint: http://eslint.org/
.. _istanbul: http://gotwarlost.github.io/istanbul/
.. _jasmine: http://jasmine.github.io/
.. _jshint: http://www.jshint.com/
.. _jslint: http://jslint.com/
.. _jquery: https://jquery.com/
.. _mocha: http://visionmedia.github.io/mocha/
.. _node.js: http://nodejs.org/
.. _phantomjs: http://phantomjs.org/
.. _qunit: https://qunitjs.com/
.. _qunit demo: http://jsfiddle.net/treyh/7kKG5/
.. _rspec: http://rspec.info/
