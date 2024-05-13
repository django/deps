=============================
DEP 0014: Background workers
=============================

:DEP: 0014
:Author: Jake Howard
:Implementation Team: Jake Howard
:Shepherd: Carlton Gibson
:Status: Draft
:Type: Feature
:Created: 2024-02-07
:Last-Modified: 2024-04-19

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

Whilst Django is a web framework, there's more to web applications than just the request-response lifecycle. Sending emails, communicating with external services or running complex actions should all be done outside the request-response cycle.

Django doesn't have a first-party solution for long-running tasks, however the ecosystem is filled with incredibly popular frameworks, all of which interact with Django in slightly different ways. Other frameworks such as Laravel have background workers built-in, allowing them to push tasks into the background to be processed at a later date, without requiring the end user to wait for them to occur.

Library maintainers must implement support for any possible task backend separately, should they wish to offload functionality to the background. This includes smaller libraries, but also larger meta-frameworks with their own package ecosystem such as `Wagtail <https://wagtail.org>`_.

This proposal sets out to provide an interface and base implementation for long-running background tasks in Django.

Specification
=============

The proposed implementation will be in the form of an application wide "task backend" interface(s). This backend will be what connects Django to the task runners with a single pattern. The task backend will provide an interface for either third-party libraries, or application developers to specify how tasks should be created and pushed into the background.

Alongside this interface, Django will provide a few built-in backends, useful for testing, local development and production use cases.

Backends
--------

A backend will be a class which extends a Django-defined base class, and provides the common interface between Django and the underlying task runner.

.. code:: python

   from datetime import datetime
   from typing import Callable, Dict, List

   from django.tasks import Task, TaskResult
   from django.tasks.backends.base import BaseTaskBackend


   class MyBackend(BaseTaskBackend):
      task_class = Task

      def __init__(self, settings_dict: Dict):
         """
         Any connections which need to be setup can be done here
         """
         super().__init__(settings_dict)

      @classmethod
      def validate_task(cls, task: Task) -> None:
         """
         Determine whether the provided task is one which can be executed by the backend.
         """
         ...

      def enqueue(self, task: Task, *args, **kwargs) -> TaskResult:
         """
         Queue up a task to be executed
         """
         ...

      def get_result(self, result_id: str) -> TaskResult:
         """
         Retrieve a result by its id (if one exists).
         If one doesn't, raises ResultDoesNotExist.
         """
         ...

      def close(self) -> None:
         """
         Close any connections opened as part of the constructor
         """
         ...


``BaseTaskBackend`` will provide ``a``-prefixed stubs for ``enqueue`` and ``get_result`` using ``asgiref.sync_to_async``.

``validate_task`` determines whether the provided ``Task`` is valid for the backend. This can be used to prevent coroutines from being executed, or otherwise validate the callable. If the provided task is invalid, it will raise ``InvalidTaskError``.

If a backend cannot support deferred tasks (ie passing the ``run_after`` argument), it should raise ``InvalidTaskError``. The ``supports_defer`` method can be used to determine whether the backend supports deferring tasks.

Django will ship with the following implementations:

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
   from typing import Callable, Self

   from django.tasks import Task, TaskResult

   class MyBackendTask(Task):
      priority: int | None
      """The priority of the task"""

      func: Callable
      """The task function"""

      queue_name: str | None
      """The name of the queue the task will run on """

      backend: str
      """The name of the backend the task will run on"""

      run_after: datetime | None
      """The earliest this task will run"""

      def using(self, priority: int | None = None, queue_name: str | None = None, run_after: datetime | timedelta | None = None) -> Self:
         """
         Create a new task with modified defaults
         """
         ...

      def enqueue(self, *args, **kwargs) -> TaskResult:
         """
         Queue up the task to be executed
         """
         ...

      def get_result(self, result_id: str) -> Self:
         """
         Retrieve a result for a task of this type by its id (if one exists).
         If one doesn't, or is the wrong type, raises ResultDoesNotExist.
         """
         ...

A ``Task`` is created by decorating a function with ``@task``:

.. code:: python

   from django.tasks import task

   @task()
   def do_a_task(*args, **kwargs):
      pass


A ``Task`` can only be created for globally-importable callables. The task will be validated against the backend's ``validate_task`` during construction.

If a task doesn't define a backend, it is assumed it will only use the default backend.

``@task`` may be used on functions or coroutines. It will be up to the backend implementor to determine whether coroutines are supported. Support for coroutine tasks can be determined with the ``supports_coroutine_tasks`` method on the backend. In either case, the function must be globally importable.

Task arguments must be JSON serializable, to avoid compatibility and versioning issues. Complex arguments should be converted to a format which is JSON-serializable.

The ``using`` method returns a clone of the task with the given attributes modified. This allows modification of the task before calling ``enqueue``. ``run_after`` cannot be passed to ``@task``, and can only be configued with ``using``.

Task Results
------------

A ``TaskResult`` is used as a handle to the running task, and contains useful information the application may need when referencing the execution of a ``Task``.

A ``TaskResult`` is obtained either when scheduling a task function, or by calling ``get_result`` on the backend. If called with a ``task_id`` which doesn't exist, a ``TaskDoesNotExist`` exception is raised.

Backend implementors aren't required to implement their own ``TaskResult``, but may for additional functionality.

.. code:: python

   from datetime import datetime
   from typing import Any, Callable

   from django.tasks import TaskResult, ResultStatus, Task

   class MyBackendTaskResult(TaskResult):
      task: Task
      """The task for which this is a result"""

      id: str
      """A unique identifier for the task result"""

      status: ResultStatus
      """The status of the running task"""

      args: list
      """The arguments to pass to the task function"""

      kwargs: dict
      """The keyword arguments to pass to the task function"""

      backend: str
      """The name of the backend the task will run on"""

      result: Any
      """The return value from the task"""

      def refresh(self) -> None:
         """
         Reload the cached task data from the task store
         """
         ...


A ``TaskResult`` will cache its values, relying on the user calling ``refresh`` to reload the values from the task store. An ``async`` version of ``refresh`` is automatically provided by ``TaskResult`` using ``asgiref.sync_to_async``.

A ``TaskResult``'s ``status`` must be one of the following values (as defined by an ``enum``):

:NEW: The task has been created, but hasn't started running yet
:RUNNING: The task is currently running
:FAILED: The task failed
:COMPLETE: The task is complete, and the ``result`` is accessible

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
--------------

Tasks can be queued using the ``enqueue`` method, which in turn calls ``enqueue`` on the task backend:

.. code:: python

   from django.tasks import task

   @task(priority=1)
   def do_a_task(*args, **kwargs):
      pass

   # Submit the task function to be run
   result = do_a_task.enqueue()

   # Optionally, provide arguments
   result = do_a_task.enqueue(1, two="three")

   # Override the priority defined by the `Task`
   result = do_a_task.using(priority=10).enqueue()

   # The modified task can be saved and reused
   do_a_high_priority_task = do_a_task.using(priority=20)
   for i in range(5):
      do_a_high_priority_task.enqueue(i)


When multiple task backends are configured, each can be obtained from a global ``tasks`` connection handler. Whilst it's unlikely multiple backends will be configured for a single project, support is available.

.. code:: python

   from django.tasks import tasks, task

   @task()
   def do_a_task(*args, **kwargs):
      pass

   # Submit the task function to be run
   result = tasks["special"].enqueue(do_a_task)

   # Optionally, provide arguments
   result = tasks["special"].enqueue(do_a_task, 1, two="three")

   # Alternatively
   result = do_a_task.using(backend="special").enqueue(1, two="three")

Whilst this API is available, it's best to call ``enqueue`` on the ``Task`` directly instead and configure the backend using the ``backend`` argument.

If a ``Task`` is defined to run on a different backend, ``InvalidTaskError`` is raised.

Deferring tasks
---------------

Tasks may also be "deferred" to run at a specific time in the future, by passing the ``run_after`` argument:

.. code:: python

   from django.utils import timezone
   from datetime import timedelta

   # Run the task at a specific time.
   result = do_a_task.using(run_after=timezone.now() + timedelta(minutes=5)).enqueue()

   # Or, pass the `timedelta` directly.
   result = do_a_task.using(run_after=timedelta(minutes=5)).enqueue()

``run_after`` must be a ``timedelta`` or timezone-aware ``datetime``.

When deferring a task, it may not be **exactly** that time a task is executed, however it should be accurate to within a few seconds. This will depend on the current state of the queue and task runners, and is out of the control of Django.

Sending emails
--------------

One of the easiest and most common places that offloading work to the background can be performed is sending emails. Sending an email requires communicating with an external, potentially third-party service, which adds additional latency and risk to web requests. These can be easily offloaded to the background.

Django will ship with an additional task-based SMTP email backend, configured identically to the existing SMTP backend. The other backends included with Django don't benefit from being moved to the background.

Async tasks
-----------

Where the underlying task runner supports it, backends may also provide an ``async``-compatible interface for task queueing, using ``a``-prefixed methods:

.. code:: python

   await do_a_task.aenqueue()
   await do_a_task.using(priority=10).aenqueue()

Similarly, a backend may support queueing an async task function:

.. code:: python

   from django.tasks import task

   @task()
   async def do_an_async_task():
      pass

   await do_an_async_task.aenqueue()

   # Also works
   do_an_async_task.enqueue()

Settings
---------

.. code:: python

   TASKS = {
      "default": {
         "BACKEND": "django.tasks.backends.ImmediateBackend",
         "QUEUES": []
         "OPTIONS": {}
      }
   }


``QUEUES`` contains a list of valid queue names for the backend. If a task is queued to a queue which doesn't exist, an exception is raised. If omitted or empty, any name is valid.

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

The API design has been intentionally designed with type-safety in mind, including support for statically validating task arguments. Using ``Task.enqueue`` allows its arguments to be statically typed, and ``using`` allows the ``Task`` to be immutable (much like ``QuerySet``). Types should be able to flow from the task function, through the ``Task`` and eventually to the ``TaskResult``.

Backwards Compatibility
=======================

So that library maintainers can use this integration without concern as to whether a Django project has configured background workers, the default configuration will use the ``ImmediateBackend``. Developers on older versions of Django but who need libraries which assume tasks are available can use the reference implementation, which will serve as a backport and be API-compatible with Django.

Reference Implementation
========================

A reference implementation is being developed alongside this DEP process. This implementation will serve as an "early-access" demo to get initial feedback and start using the interface, as the basis for the integration with Django itself, but also as a backport for users of supported Django versions prior to this work being released.

The reference implementation can be found at https://github.com/RealOrangeOne/django-core-tasks, along with its progression.

Future iterations
=================

The field of background tasks is vast, and attempting to implement everything supported by existing tools in the first iteration is futile. The following functionality has been considered, and deemed explicitly out of scope of the first pass, but still worthy of future development:

- Completion / failed hooks, to run subsequent tasks automatically
- Bulk queueing
- Automated task retrying
- A generic way of executing task runners. This will remain the responsibility of the underlying implementation, and the user to execute correctly.
- Observability into task queues, including monitoring and reporting
- Cron-based scheduling
- Task timeouts
- Swappable argument serialization (eg `pickle`)

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).
