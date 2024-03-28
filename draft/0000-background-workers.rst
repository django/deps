=============================
DEP XXXX: Background workers
=============================

:DEP: XXXX
:Author: Jake Howard
:Implementation Team: Jake Howard
:Shepherd: Carlton Gibson
:Status: Draft
:Type: Feature
:Created: 2024-02-07
:Last-Modified: 2024-02-09

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

Django doesn't have a first-party solution for long-running tasks, however the ecosystem is filled with incredibly popular frameworks, all of which interact with Django in slightly different ways. Other frameworks such as Laravel have background workers built-in, allowing them to push tasks into the background to be processed at a later date, without requiring the end user to wait for them to occur.

Library maintainers must implement support for any possible task backend separately, should they wish to offload functionality to the background. This includes smaller libraries, but also larger meta-frameworks with their own package ecosystem such as `Wagtail <https://wagtail.org>`_.

Specification
=============

The proposed implementation will be in the form of an application wide "task backend" interface. This backend will be what connects Django to the task runners with a single pattern. The task backend will provide an interface for either third-party libraries, or application developers to specify how tasks should be created and pushed into the background.

Backends
--------

A backend will be a class which extends a Django-defined base class, and provides the common interface between Django and the underlying task runner.

.. code:: python

   from datetime import datetime
   from typing import Callable, Dict, List

   from django.tasks import Task, TaskResult
   from django.tasks.backends.base import BaseTaskBackend


   class MyBackend(BaseTaskbackend):
      task_class = Task

      def __init__(self, options: Dict):
         """
         Any connections which need to be setup can be done here
         """
         super().__init__(options)

      @classmethod
      def is_valid_task(cls, task: Task) -> bool:
         """
         Determine whether the provided task is one which can be executed by the backend.
         """
         ...

      def enqueue(self, task: Task, *, args: List, kwargs: Dict, priority: int | None = None, run_after: datetime | None = None) -> TaskResult:
         """
         Queue up a task to be executed
         """
         ...

      def get_task(self, task_id: str) -> TaskResult:
         """
         Retrieve a task by its id (if one exists).
         If one doesn't, raises TaskDoesNotExist.
         """
         ...

      def close(self) -> None:
         """
         Close any connections opened as part of the constructor
         """
         ...


``BaseTaskBackend`` will provide ``a``-prefixed stubs for ``enqueue`` and ``get_task`` using ``asgiref.sync_to_async``.

If a backend receives a task which is not valid (ie ``is_valid_task`` returns ``False``), it should raise ``InvalidTaskError``.

If a backend cannot support deferred tasks (ie passing the ``run_after`` argument), it should raise ``InvalidTaskError``. The ``supports_defer`` method can be used to determine whether the backend supports deferring tasks.

``is_valid_task_function`` determines whether the provided function (or possibly coroutine) is valid for the backend. This can be used to prevent coroutines from being executed, or otherwise validate the callable.

Django will ship with 3 implementations:

ImmediateBackend
   This backend runs the tasks immediately, rather than offloading to a background process. This is useful both for a graceful transition towards background workers, but without impacting existing functionality.

DatabaseBackend
   This backend uses the Django ORM as a task store. This backend will support all features, and should be considered production-grade.

DummyBackend
   This backend doesn't execute tasks at all, and instead stores the ``Task`` objects in memory. This backend is mostly useful in tests.

Tasks
-----

A ``Task`` is the action which the task runner will execute. It is a class which holds a callable and some defaults for ``enqueue``.

Backend implementors aren't required to implement their own ``Task``, but may for additional functionality.

.. code:: python

   from datetime import datetime
   from typing import Callable

   from django.tasks import Task

   class MyBackendTask(Task):
      priority: int | None
      """The priority of the task"""

      func: Callable
      """The task function"""

      args: list
      """The arguments to pass to the task function"""

      kwargs: dict
      """The keyword arguments to pass to the task function"""


A ``Task`` is created by decorating a function with ``@task``:

.. code:: python

   from django.tasks import task

   @task()
   def do_a_task(*args, **kwargs):
      pass


A ``Task`` can only be created for globally-importable callables. The task will be validated against the backend's ``is_valid_task`` callable during construction.

``@task`` may be used on functions or coroutines. It will be up to the backend implementor to determine whether coroutines are supported. In either case, the function must be globally importable.

Task Results
------------

A ``TaskResult`` is used as a handle to the running task, and contains useful information the application may need when referencing the execution of a ``Task``.

A ``TaskResult`` is obtained either when scheduling a task function, or by calling ``get_task`` on the backend. If called with a ``task_id`` which doesn't exist, a ``TaskDoesNotExist`` exception is raised.

Backend implementors aren't required to implement their own ``TaskResult``, but may for additional functionality.

.. code:: python

   from datetime import datetime
   from typing import Callable

   from django.tasks import TaskResult, TaskStatus, Task

   class MyBackendTaskResult(TaskResult):
      task: TaskResult
      """The task of which this is a result"""

      priority: int | None
      """The priority of the task"""

      run_after: datetime | None
      """The earliest time the task will be executed"""

      status: TaskStatus
      """The status of the running task"""

      def refresh(self) -> None:
      """
      Reload the cached task data from the task store
      """
      ...


Attributes such as ``priority`` will reflect the values used to enqueue the task, as opposed to the defaults from the ``Task``. If no overridden values are provided, the value will mirror the ``Task``.

A ``TaskResult`` will cache its values, relying on the user calling ``refresh`` to reload the values from the task store. An ``async`` version of ``refresh`` is automatically provided by ``TaskResult`` using ``asgiref.sync_to_async``.

A ``TaskResult``'s ``status`` must be one of the following values (as defined by an ``enum``):

:NEW: The task has been created, but hasn't started running yet
:RUNNING: The task is currently running
:FAILED: The task failed
:COMPLETE: The task is complete, and the result is accessible

If a backend supports more than these statuses, it should compress them into one of these.

For convenience, calling a ``TaskResult`` will execute the task's function directly, which allows for graceful transitioning towards background tasks:

.. code:: python

   from django.tasks import task

   @task()
   def do_a_task(*args, **kwargs):
      pass

   # Calls `do_a_task` as if it weren't a task
   do_a_task()

Queueing tasks
-------------

Tasks can be queued using ``enqueue``, a proxy method which calls ``enqueue`` on the default task backend:

.. code:: python

   from django.tasks import enqueue, task

   @task(priority=1)
   def do_a_task(*args, **kwargs):
      pass

   # Submit the task function to be run
   task = enqueue(do_a_task)

   # Optionally, provide arguments
   task = enqueue(do_a_task, args=[], kwargs={})

   # Override the priority defined by the `Task`
   task = enqueue(do_a_task, priority=10)

When multiple task backends are configured, each can be obtained from a global ``tasks`` connection handler. Whilst it's unlikely multiple backends will be configured for a single project, support is available.

.. code:: python

   from django.tasks import tasks, task

   @task
   def do_a_task(*args, **kwargs):
      pass

   # Submit the task function to be run
   task = tasks["special"].enqueue(do_a_task)

   # Optionally, provide arguments
   task = tasks["special"].enqueue(do_a_task, args=[], kwargs={})

When enqueueing tasks, ``args`` and ``kwargs`` are intentionally their own dedicated arguments to make the API simpler and backwards-compatible should other attributes be added in future.

Deferring tasks
---------------

Tasks may also be "deferred" to run at a specific time in the future, by passing the ``run_after`` argument:

.. code:: python

   from django.utils import timezone
   from datetime import timedelta
   from django.tasks import enqueue

   task = enqueue(do_a_task, run_after=timezone.now() + timedelta(minutes=5))

``run_after`` must be a timezone-aware ``datetime``.

When deferring a task, it may not be **exactly** that time a task is executed, however it should be accurate to within a few seconds. This will depend on the current state of the queue and task runners, and is out of the control of Django.

Sending emails
--------------

One of the easiest and most common places that offloading work to the background can be performed is sending emails. Sending an email requires communicating with an external, potentially third-party service, which adds additional latency and risk to web requests. These can be easily offloaded to the background.

Django will ship with an additional task-based SMTP email backend, configured identically to the existing SMTP backend. The other backends included with Django don't benefit from being moved to the background.

Async tasks
-----------

Where the underlying task runner supports it, backends may also provide an ``async``-compatible interface for task queueing, using ``a``-prefixed methods:

.. code:: python

   from django.tasks import aenqueue

   await aenqueue(do_a_task)

Similarly, a backend may support queueing an async task function:

.. code:: python

   from django.tasks import aenqueue, enqueue, task

   @task()
   async def do_an_async_task():
      pass

   await aenqueue(do_an_async_task)

   # Also works
   enqueue(do_an_async_task)

Settings
---------

.. code:: python

   TASKS = {
      "default": {
         "BACKEND": "django.tasks.backends.ImmediateBackend",
         "OPTIONS": {}
      }
   }

``OPTIONS`` is passed as-is to the backend's constructor.

Motivation
==========

Having a first-party interface for background workers poses 2 main benefits:

Firstly, it lowers the barrier to entry for offloading computation to the background. Currently, a user needs to research different worker technologies, follow their integration tutorial, and modify how their tasks are called. Instead, a developer simply needs to install the dependencies, and work out how to *run* the background worker. Similarly, a developer can start determining which actions should run in the background before implementing a true background worker, and avoid refactoring should the backend change over time.

Secondly, it allows third-party libraries to offload some of their execution. Currently, library maintainers need to either accept their code will run inside the request-response lifecycle, or provide hooks for application developers to offload actions themselves. This can be particularly helpful when offloading certain expensive signals.

One of the key benefits behind background workers is removing the requirement for the user to wait for tasks they don't need to, moving computation and complexity out of the request-response cycle, towards dedicated background worker processes. Moving certain actions to be run in the background not improves performance of web requests, but also allows those actions to run on specialised hardware, potentially scaled differently to the web servers. This presents an opportunity to greatly decrease the percieved execution time of certain common actions performed by Django projects.

The target audience for ``DatabaseBackend`` and a SQL-based queue are likely fairly well aligned with those who may choose something like PostgreSQL FTS over something like ElasticSearch. ElasticSearch is probably better for those 10% of users who really need it, but doesn't mean the other 90% won't be perfectly happy with PostgreSQL, and probably wouldn't benefit from ElasticSearch anyway.

But what about *X*?
-------------------

The most obvious alternative to this DEP would be to standardise on a task implementation and vendor it in to Django. The Django ecosystem is already full of background worker libraries, eg Celery and RQ. Writing a production-ready task runner is a complex and nuanced undertaking, and discarding the work already done is a waste.

This proposal doesn't seek to replace existing tools, nor add yet another option for developers to consider. The primary motivation is creating a shared API contract between worker libraries and developers. It does however provide a simple way to get started, with a solution suitable for most sizes of projects (``DatabaseBackend``). Slowly increasing features, adding more built-in storage backends and a first-party task runner aren't out of the question for the future, but must be done with careful planning and consideration.

Rationale
=========

This proposed implementation specifically doesn't assume anything about the user's setup. This not only reduces the chances of Django conflicting with existing task systems a user may be using (eg Celery, RQ), but also allows it to work with almost any hosting environment a user might be using.

This proposal started out as `Wagtail RFC 72 <https://github.com/wagtail/rfcs/pull/72>`_, as it was becoming clear a unified interface for background tasks was required, without imposing on a developer's decisions for how the tasks are executed. Wagtail is run in many different forms at many different scales, so it needed to be possible to allow developers to choose the backend they're comfortable with, in a way which Wagtail and its associated packages can execute tasks without assuming anything of the environment it's running in.

The global task connection ``tasks`` is used to access the configured backends, with global versions of those methods available for the default backend. This contradicts the pattern already used for storage and caches. A "task" is already used in a number of places, so using it to refer to the default backend is confusing and may lead to it being overridden in the current scope:

.. code:: python

   from django.tasks import tasks

   # Later...
   result = tasks.enqueue(do_a_thing)

   # Clearer
   thing_result = tasks.enqueue(do_a_thing)

Backwards Compatibility
=======================

So that library maintainers can use this integration without concern as to whether a Django project has configured background workers, the default configuration will use the ``ImmediateBackend``. Developers on older versions of Django but who need libraries which assume tasks are available can use the reference implementation.

Reference Implementation
========================

The reference implementation will be developed alongside this DEP process. This implementation will serve both as an "early-access" demo to get initial feedback and start using the interface, as the basis for the integration with Django core, but also as a backport for users of supported Django versions prior to this work being released.

A more complete implementation picture can be found at https://github.com/RealOrangeOne/django-core-tasks, however it should not be considered final.

Future iterations
=================

The field of background tasks is vast, and attempting to implement everything supported by existing tools in the first iteration is futile. The following functionality has been considered, and deemed explicitly out of scope of the first pass, but still worthy of future development:

- Completion hooks, to run subsequent tasks automatically
- Bulk queueing
- Automated task retrying
- A generic way of executing task runners. This will remain the responsibility of the underlying implementation, and the user to execute correctly.
- Observability into task queues, including monitoring and reporting
- Cron-based scheduling

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).
