=======================================
DEP 8: Gathering Django usage analytics
=======================================

:DEP: 8
:Author: Jacob Kaplan-Moss
:Implementation Team: TBD
:Shepherd: TBD
:Status: Draft
:Type: Feature/Process
:Created: 2016-11-05
:Last-Modified: 2016-11-05

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

    Maintaining open source code used to be more manageable. [...]

    Today, everybody uses open source code, including Fortune 500 companies,
    government, major software companies and startups. Sharing, rather than
    building proprietary code, turned out to be cheaper, easier, and more
    efficient. This increased demand puts additional strain on those who
    maintain this infrastructure, yet because these communities are not highly
    visible, the rest of the world has been slow to notice. Most of us take
    opening a software application for granted, the way we take turning on the
    lights for granted. We don’t think about the human capital necessary to make
    that happen. 

    In the face of unprecedented demand, the costs of not supporting our digital
    infrastructure are numerous.

    — Nadia Eghbal, `Roads and Bridges: The Unseen Labor Behind Our Digital Infrastructure <http://www.fordfoundation.org/library/reports-and-studies/roads-and-bridges-the-unseen-labor-behind-our-digital-infrastructure/>`_.

..

    A lot of people contribute to OSS in their free time and do it because they
    generally enjoy it. [...]  Ask any open source project
    maintainer, though, and they will tell you about the reality of the amount
    of work that goes into managing a project. You have clients. You are fixing
    issues for them. You are creating new features. This becomes a real demand
    on your time.

    Paid or not, play or not, this is labor that is currently not being
    compensated.

    — Ashe Dryden, `The Ethics of Unpaid Labor and the OSS Community <https://www.ashedryden.com/blog/the-ethics-of-unpaid-labor-and-the-oss-community>`_.

As Django enters its second decade, we're thinking about the long game.
Sustainability has become a key concern. Django is indeed used by  "Fortune 500
companies, government, major software companies and startups", yet those
organizations mostly don't contribute meaningfully to Django's continued
success. The majority of work is at the whim of volunteers and their free time.

Increasingly, we've recognized that this is not sustainable. Relying on the
free labor of volunteers is ineffective, unfair, and risky. Put bluntly:
**the future of Django depends on our ability to fund its development**.

In the last few years, we've started taking steps to fund important work. The
Django Software Foundation now employs an engineer to shepherd Django's
development, and this has been wildly successful in improving Django's velocity,
reducing bugs, and shipping releases on-time. Additionally, several major new
features in Django were funded through some mix of corporate sponsorship,
grants, or crowdfunding.

These funded projects have been quite successful, but this success is tenuous.
Most work is still volunteer-driven, and those who are paid by and large have
been paid well below market rates. 

This is because fundraising is extremely difficult: it's hard to convince
organizations to spend money on something they get for free.

A major reason that fundraising remains difficult is our inability to measure
the size of the Django community. The only information we have about the use of
Django is anecdotal (e.g. "Instagram uses Django") or is measuring information
without much value (e.g. number of times Django's been installed, which is
essentially a vanity metric inflated by virtual environments, CI servers, and
the like). If we had clear data on the extent of Django's usage, it would be
much easier to approach organizations for funding. As Eghbal writes:

    [W]ithout data about which tools are used, and how much we rely upon them,
    [it is hard to paint a clear picture of what is underfunded.

    With better metrics, we could describe the economic impact of digital
    infrastructure, identify critical projects that are lacking support, and
    understand dependencies between projects and people. Right now, it is
    impossible to say who is using an open source project unless that person or
    company discloses their usage. Our information about which projects need
    better support is mostly anecdotal.

Anyone who's tried to raise money for Django knows this first-hand: potential
sponsors always ask for data. When they hear that we have no hard metrics,
their offers decrease (or vanish).

We aim to solve this problem by starting gathering anonymous usage metrics. We
know that this is touchy -- privacy is an important value in our community, and
we're not interested in tracking our users. However, we need this data to
make the case to companies and governments for increased funding.

We believe that we've struck a balance that lets us gather the data we need
for sustainability while respecting our users' privacy. And, it'll always
be possible for users to disable this metric collection. We're hoping the vast
majority of our users will choose to leave it enabled as a small but important
way of helping Django continue to thrive.

The rest of this DEP explains what we measure and how that data is used.

Specification
=============

Starting in version XXX, Django gathers anonymous user analytics and report
those to Google Analytics. This will happen when certain ``django-admin``
commands are run. Metric collection will be enabled by default, and users 
will be warned the first time they run ``django-admin``.

When will analytics be sent?
----------------------------

Analytics will be sent when certain ``django-admin`` commands are run:
``startproject``, ``startapp``, and ``runserver``. If a settings file
can be loaded (i.e. for``startapp`` and ``runserver``), analytics will only
be gathered and sent if ``DEBUG`` is ``True``.

Our goal is to try to measure "unique developers", so we've tried to select
commands that will only be run in development situations, and won't be run by
production servers. By selecting a few different commands, we account for a
variety of developer workflows.

What is tracked?
----------------

Django sends an ``event`` hit type when you run one of the above commands.
This event includes the following information:

- An event category corresponding to the specific command run (e.g. 
  ``startproject``, ``startapp``, or ``runserver``). No arguments to 
  the command are sent (so we don't receive the project name or app name,
  where the server is running, etc.)

- A HTTP User-Agent that identifies the version of Django, the version of
  Python, and a platform identifier. For example: 
  ``Django/1.11 CPython/3.5.1 (Macintosh; Intel macOS 10.12.0)``

- The Django name (e.g. ``Django``) and version (e.g. ``1.11``) passed as
  the Google Analytics application name (`aid`_) and application version (`av`_).

- A unique Django analytics user ID, e.g. ``3fa04034-a36b-11e6-acd6-acbc32c6febd``.
  This is generated by the Python standard library function ``uuid.uuid1()`` and
  stored in ``~/.config/djangoanalytics`` (or equivalent on non-Linux
  platforms). This means we can't track individual users, but does enable us to
  more accurate measure distinct user counts vs. event accounts. This is sent as
  the Google Analytics `cid parameter`_.

  Note that we can't actually see this ID -- it's used anonymously to identify
  a single user, but isn't exposed in Google Analytics. This means we can't
  tie an event to a single user, even if we wanted to -- which we most certainly
  do not. 

- The flag to enable IP anonymization, which ensures that we can't see, and 
  Google Analytics doesn't store, your actual IP. This is done by setting the
  Google Analytics `aip parameter`_ to ``1``.

- The Google Analytics version - ``1`` . This is sent as the Google Analytics 
  `v parameter`_. 

- Django's Google Analytics tracking ID - e.g. ``UA-XXXXXXXX-X``.
  This is sent as the Google Analytics `tid parameter`_.

.. _cid parameter: https://developers.google.com/analytics/devguides/collection/protocol/v1/parameters#cid
.. _v parameter: https://developers.google.com/analytics/devguides/collection/protocol/v1/parameters#v
.. _tid parameter: https://developers.google.com/analytics/devguides/collection/protocol/v1/parameters#tid
.. _aip parameter: https://developers.google.com/analytics/devguides/collection/protocol/v1/parameters#aip
.. _aid: https://developers.google.com/analytics/devguides/collection/protocol/v1/parameters#aid
.. _av: https://developers.google.com/analytics/devguides/collection/protocol/v1/parameters#av

You can view all information that is sent by setting ``DJANGO_ANALYTICS_DEBUG=1``
in your environment. This'll print analytics to the console instead of sending
them to Google Analytics.

.. note::

    This section is largely cribbed from `Homebrew's analytics implementation <https://github.com/Homebrew/brew/blob/bbed7246bc5c5b7acb8c1d427d10b43e090dfd39/docs/Analytics.md>`_. Thanks!

How will analytics be sent?
---------------------------

Data is sent to Google Analytics over HTTPs using Python's ``urllib2`` standard
library.

Who has access to analytics data?
---------------------------------

Access to the Google Analytics dashboard and data will be limited to the 
following people/groups:

- The DSF President, in their role providing oversight to the DSF.

- Members of a fundraising committee, if established by the DSF Board. Employees
  or contractors hired for fundraising purposes may also be granted access by
  this fundraising committee.

- Members of the Django Technical Board, upon request.

- Members of the Django Infrastructure Team (so they can maintain the GA 
  instance and grant/revoke access). These will be the only administrative
  users (i.e., the only users who can grant or revoke access).

Opting out
----------

Users can disable analytics collection in two ways:

1. By setting an environment variable: ``export DJANGO_NO_ANALYTICS=1``.

2. Setting ``disable=1`` in ``~/.config/djangoanalytics`` (or equivalent).

The first time Django tries to send analytics for a given user, it'll 
print out a message about metrics collection with instructions for disabling it.

Implementation
--------------

Once the implementation is merged, it'll be linked up here. In the meantime,
see the `Reference Implementation`_ section for a rough picture.

Rationale
=========

The high-level rationale is explained in the `Abstract`_: gather data that  we
can use to convince organizations to support Django. This section articulates
the detailed decisions we made to get from that high-level goal to this specific
implementation.

Other options for what to collect and measure
---------------------------------------------

The number we'd *really* like to have is the number of production websites or
servers running Django. We could gather this by sending metrics data when a
Django worker is started -- for example, from within ``django.setup()``, or
or when the WSGI application is initialized. 

However, this would be unacceptable to many organizations. Application servers
"phoning home" raise serious security concerns, and many larger organizations
consider information on their production environments to be confidential. So,
as much as we want this data, collecting it is simply too invasive.

Another option would be to collect data on the admin usage (e.g. embedding
Google Analytics directly). A couple of Django projects (Wagtail and Oscar)
have done this successfully. We decided against this since "people
who use the admin" isn't as useful a metric as counting developers.

Finally, we considered tracking *all* ``django-admin`` commands, which would  do
a better job of finding developers (not everyone uses ``startproject``,
``startapp``, or ``runserver``). However, would risk getting run on production
servers -- for example, many people run ``migrate`` on their production servers
-- which raise some of the same concerns as above. So, we choose to only measure
upon certain commands that we can feel fairly certain won't be run in production.
This runs the risk of undercounting, but we think this is the best option.

Opt-out vs opt-in
-----------------

We chose to send analytics data by default, with a way to opt out. Another
option would be an opt-in system, along the lines of Debian's `popularity
contest <http://popcon.debian.org/>`_.

The downsides of this approach is that it severely undercounts: the only
people who will turn something like this on are "true fans". So, an opt-in
approach isn't substantially better than a community survey. We've run these
in the past, and while they've given data that we've found interesting, 
potential sponsors have been far less impressed by that data.

We believe that collecting data by default is the only way we'll get a roughly
accurate measure of Django's usage.

Google Analytics vs other platforms/choices
-------------------------------------------

Using Google Analytics is a trade-off. On the one hand, Google's track record 
indicates that they don't value privacy nearly as high as we do. However, 
running our own analytics collection and analysis will make our sustainability
problem worse, and the entire point of doing this is to make it better. And,
if we're going to use a third-party tracking vendor, Google is the best
one out there.

We've carefully chosen what to send to GA so that even if Google turns evil
they couldn't track Django users. As far as we can tell, the only thing Google
could do would be to lie about anonymizing IP addresses, and attempt to match
users based on their IPs. If we discovered Google was lying about this,
we'd obviously stop using them immediately.

Reference Implementation
========================

TBD.

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).

(All DEPs must include this exact copyright statement.)