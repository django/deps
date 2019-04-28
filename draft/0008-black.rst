====================================
DEP 0008: Formatting Code with Black
====================================

:DEP: 0008
:Author: Aymeric Augustin
:Implementation Team: Aymeric Augustin, Carlton Gibson, Florian Apolloner, Herman Schistad, Markus Holtermann
:Shepherd: Andrew Godwin
:Status: Draft
:Type: Process
:Created: 2019-04-27
:Last-Modified: 2019-04-28

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

This DEP proposes to enforce code formatting with Black_ in Django.

.. _Black: https://github.com/ambv/black

Foreword
========

Code formatting is the ultimate bikeshed_. Perfectionists have strong feelings
about the aesthetics of laying out the tokens that make a Python program in
the window of a text editor.

Within the principles of :pep:`8`, there's quite a bit of room for formatting
code in various ways. Even these principles aren't fully consensual, notably
the rules about hanging indents — that's why flake8 disables `controversial
rules`_ by default.

The `django-developers thread`_ about Black was the largest by number of
messages in several months. Any proposal in this area will have enthusiastic
proponents and sincere opponents. Consensus is an elusive goal when personal
taste is such a large factor.

I'm writing this DEP because, based on my experience with other open-source
projects and the community feedback I received — in public or in private —
I believe that adopting Black would be a worthwhile improvement for Django.

Keep in mind that this isn't a make-or-break decision for Django. It's about
making it more convenient to contribute, especially for new or occasional
contributors who haven't internalized current code formatting standards.

Like most changes to entrenched habits, it's a trade-off between current
contributors and future contributors, where current contributors get to make
the decision.

Even though this DEP argues in favor of Black, I made an effort to represent
both sides of the debate fairly, with relevant quotes from the
django-developers discussion.

Please read it with an open mind :-)

.. _bikeshed: http://bikeshed.com/
.. _controversial rules: https://gitlab.com/pycqa/flake8/blob/88caf5ac484f5c09aedc02167c59c66ff0af0068/src/flake8/defaults.py#L15
.. _django-developers thread: https://groups.google.com/d/msg/django-developers/wK2PzdGNOpQ/DG55Ai0EBQAJ

Specification
=============

All Python code in Django is formatted with Black_, using its default
settings, that is, 88 characters per line and double quotes.

Official Django projects are encouraged to adopt the same policy. Some already
do, for example channels_ and asgiref_.

.. _channels: https://github.com/django/channels
.. _asgiref: https://github.com/django/asgiref

Motivation
==========

There's no debate about the usefulness of **readable code formatting**. While
it doesn't change the semantics of the code, it simplifies future maintenance.
Since code is read much more often than it is written, it makes sense to
invest some effort when writing code to make it easier to read later.

Until now this effort has been performed by humans, mostly based on :pep:`8`,
a rather long document. Memorizing and applying properly all these rules isn't
the most exciting part of contributing to Django, to say the least.

Furthermore, code formatting can create a barrier for new contributors, if
they think they can't write code that looks as good as pull requests from
other contributors. This is particularly true for new contributors, who are
increasingly hard to attract as Django grows more mature.

With **automated code formatting**, this workload can be transferred to
computers, saving human bandwidth for higher value-added activities.

Generally speaking, there are two major benefits to automated code formatting:

* Individually, developers no longer have to constantly make small decisions
  about code formatting, based on rules, on taste, or on a mix of both. Just
  throw the code in a file, run the formatter, done!

  You don't realize how much this reduces decision fatigue until you try it.
  It's a real boon to those, like me, who spend way too much time fine-tuning
  the formatting of their code.

* Collectively, contributors no longer need to think about code formatting
  in code reviews. Whatever the formatter does is the expected result, by
  definition.

  This removes the thought stream of "mmm, I would have formatted this a bit
  differently" while reviewing code exactly like it removes "mmm, how do I
  format this?" while writing code.

Or, to put it more concisely: "Not needing to think much about code style when
writing code or when reviewing is very nice." - Ian Foote

Specifically for Django, I would add a third major benefit:

* Would-be contributors have one fewer hurdle to jump to create a merge-ready
  pull request. Even committers with a decade of experience writing code for
  Django say the back and forth of style reviews can be annoying!

  Django has over a thousand open accepted tickets, many of which aren't very
  hard and just need focused effort on a small area. (Look at the admindocs
  tickets for example.) At the same time, many people express a desire to get
  involved and yet don't.

  The stringent review process, while critical for quality, is a barrier to
  entry. It seems silly that formatting would put people off, but it does.
  Making it a non-issue would help.

In the words of a contributor: "One of the main frustration points I've had
when making a contribution is having to fix small formatting errors. (...) It
produces a lot of inertia and can stop PRs from getting merged for extended
periods of time. So from a new contributor angle I think Black is an obvious
choice." - Nick Sarbicki

Finally, automated code formatting will increase consistency across the Django
code base. Currently the style of each module shows roughly when it was
written or rewritten. Having a unified style will reduce the friction of
adjusting to the style of each module. This is a nice side effect.

Given these benefits, if formatting code was an entirely mechanical process,
it would have been automated long ago! Unfortunately, it's hard to design an
algorithm that works sufficiently well for all practical cases.

Black is the first Python code formatter that produces good enough results and
demonstrates significant traction in open source projects.

Therefore, this DEP proposes to adopt Black for Django.

Rationale
=========

If you're reading this, I assume that you familiarized yourself with Black and
that I don't need to explain its philosophy.

The discussion of adopting Black for Django revolves around two topics:

1. Process: there's consensus that automated code formatting would greatly
   facilitate the development of Django;
2. Results: there's no consensus at the time of writing: some people like
   what Black produces, others don't.

Process
-------

There's consensus in favor of automated code formatting, even if different
people assign different weight to each reason laid out in the "Motivation"
section above.

Even those who oppose Black or express skepticism recognize the advantages.
Here are relevant quotes from the django-developers discussion:

* "I'm not sure I like Black per se, but using an auto-formatter would enable
  review comments to focus on substantive points." - Carlton Gibson

* "I like the *idea* of an autoformatter. I dislike the particular
  mostly-unconfigurable style Black enforces, and I find that several of its
  rules negatively impact code readability." - James Bennett

* "I see the benefits [lower barrier to entry, time saving for the Fellows,
  etc], but I don't believe Black is the answer." - Curtis Maloney

So this point is well established.

Results
-------

Opinions are mixed regarding the quality of what Black produces.

Obviously Black gives consistent results faster than humans. This may not seem
useful to contributors with enough Python experience to format code pretty
much like Black would without much effort. It's more valuable to contributors
who haven't reached that stage yet. It levels the coding field.

Humans are very sensitive to cases where a computer does worse than humans,
even if the computer does better on average. The occasional *obviously wrong*
result has a devastating effect on the acceptability of automation. This is
the most common argument brought against Black.

(And it is in no way specific to Black. All automation efforts in the history
of humanity must have received similar criticism at some point.)

Several developers report that, in their experience, Black made code
formatting worse and decreased readability. Concrete examples shown in the
discussion were short lists, which Black reformats when they fit on a single
line, and vertically aligned comments, which Black is unable to preserve.
Generally, the way Black fits expressions on a single line seems to be a
sticking point. Many developers feel strongly about retaining control over
vertical formatting.

These issues don't seem critical enough to rule out Black. At worst, it could
be disabled locally with ``# fmt: off`` and ``# fmt: on`` if it gets the
formatting of a block of code egregiously wrong.

Others explained that, after an initial knee-jerk reaction against change,
they started to like Black's choices. For example:

* "As for disagreeing with some of Black's choices - you learn very quickly to
  live with those choices, and forget those choices. (...) I'm in favour of
  using Black's double quotes for strings. I **hated** this decision when it
  was first made, but have seriously come around to it, and prefer it
  aesthetically too." - Josh Smeaton

* "I've used Black extensively on several projects, and much like f-strings,
  the last Pink Floyd album, and broccoli, have found I really like something
  I didn't think I would." - Tim Allen

* "I'm one of those people who hesitated because I didn't like many of the
  choices Black made but I adapted really quickly." - Matthias Kestenholz

Looking at how Black reformats a few files from the Django source tree, I'm
impressed by how few changes it makes. What Black produces is very close to
the current Django coding style. That should make its adoption painless.

The obvious exception is quotes. Black standardizes on double quotes while
Django uses single and double quotes inconsistently. Some parts of Django —
including parts I wrote more recently — use single quotes for machine-readable
identifiers and double quotes for human-readable language. In hindsight, this
convention is too hard to enforce to be worth the effort, all the more since
it isn't generalized. Going forwards, normalizing to double quotes like Black
does by default will keep things simple.

My best guess is that Black will make code formatting a bit better on average,
despite occasional sub-optimal results. Others may feel more strongly about
their personal preferences that diverge from what Black does. However, I don't
think personal preferences should outweigh growing community standards.

Ultimately, given how much this is a matter of personal judgement, perhaps the
best attempt at consensus would be to state that the formatting produced by
Black doesn't make a decisive change, positive or negative, to our ability to
maintain Django.

Other concerns
--------------

At the time of writing, Black is in beta, meaning that the formatting it
produces could still change. Its 1.0 version is expected any time now. When
this DEP is accepted (if it is), Black should be stable, most likely without
significant changes from the current beta.

Reformatting the entire code base with Black will touch most files and change
many lines without altering their meaning. This will pollute the git history.
However, formatting changes already happen alongside new features and bug
fixes, adding a steady stream of pollution. Adopting Black will eliminate
future code reformatting, making the git history cleaner looking forwards.
Besides, GitHub has a "see the blame before this commit" button to jump easily
through refactoring commits.

This commit will also be disruptive for open pull requests. One way to update
them is to run Black on modified files, keep a copy aside, start a new branch
from master, move the modified files back into place, and commit the result.

In order to minimize the effort for backporting patches, Black will be applied
to the master and stable/2.2.x branches, which are in their mainstream support
period. 2.2 is an LTS release that will be supported for three more years;
this is a good reason for formatting it. Black will not be applied to
stable/2.1.x and stable/1.11.x which are in the extended support period and
only get fixes for security and data loss bugs.

Alternatives
------------

Three major Python code formatters exist: autopep8, yapf and Black.

No one argued in favor autopep8. Also I believe Black's approach is superior.

It was suggested that yapf could be configured to produce results closer to
Django's current style. I don't think that's worth pursuing for three reasons:

* The point of adopting an automatic code formatter isn't to have our own
  Django-flavored code formatting style. It's about making our Python code
  look as much as possible like what everyone else in the Python community
  writes. Code formatters maximize their usefulness by not being configurable.

* Reaching consensus in open source communities is hard — I'm investing more
  than a day in writing this DEP! — which makes it essential to minimize
  choices. This must be why non-configurable formatters such as Prettier and
  Black have seen fast adoption by open source projects.

* Black produces formatting that is so close to Django's current standards
  that there seems to be very little value in tuning a yapf configuration to
  produce something even closer.

Summary
-------

To sum up:

1. Applying Black to the source code of Django won't make formatting
   drastically better or worse;

2. Integrating Black in the development process of Django has very
   significant benefits;

3. These benefits clearly outweigh code formatting style considerations.

One final quote: "The best thing about automatic formatters, in my
opinion, is even if you don't like the style at least you don't have to talk
about it anymore! And you tend to get used to it eventually." - Sam Cooke

Backwards Compatibility
=======================

This DEP doesn't introduce any backwards incompatibilities.

Black guarantees that it doesn't change the behavior of the code by checking
that processing a file doesn't change its AST_.

.. _AST: https://docs.python.org/3/library/ast.html

Reference Implementation
========================

Implementing this change requires:

1. Updating the `coding style`_:

   * Adding documentation about Black, similar to the existing documentation
     about isort;
   * Updating explanations around :PEP:`8` and flake8 — they cover a lot more
     that code formatting so they remain useful even with Black;
   * Removing other references to code formatting, like the specification of
     the favorite hanging indent style and chained calls style.

.. _coding style: https://docs.djangoproject.com/en/2.2/internals/contributing/writing-code/coding-style/

2. Updating flake8 and isort configuration to be compatible with Black.

   This is straightforward and well documented.

3. Formatting the code. This will be done in three steps for each branch:

   * Identify if Black produces an egregiously bad result on some files. For
     example, the date and time formats files were noted as possible problems.
     Exclude these files with ``# fmt: off`` and ``# fmt: on`` comments.

   * Run Black on the entire Django code repository and make a single commit,
     which will look like this: https://github.com/hermansc/django/pull/1.

     Since the change will be fully automated, there won't be anything to
     review, so it's easier to make just one commit. That commit will be easy
     to identify as non-significant in the future.

   * Attempt to refactor excluded files, perhaps by moving comments, no that
     Black can do a decent job on them. Commit this separately. This isn't
     strictly necessary. It can be done at any later point.

4. Enforcing Black in CI. This means:

   * Adding a black builder to Jenkins, based on the isort builder;
   * Adding a black job to tox.ini.

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).
