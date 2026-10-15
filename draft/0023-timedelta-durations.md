---
DEP: 0023
Author: Johannes Maron
Implementation Team: TBD
Shepherd: TBD
Status: Draft
Type: Feature
Created: 2026-09-25
---
# DEP 0023: Explicit, unit-aware durations via `datetime.timedelta`

Table of Contents
- [Abstract](#abstract)
- [Specification](#specification)
  - [The duration type](#the-duration-type)
  - [Sentinels](#sentinels)
  - [Backwards compatible normalization](#backwards-compatible-normalization)
  - [The affected surface](#the-affected-surface)
  - [Defaults](#defaults)
  - [Names](#names)
  - [Zero, negative, and unbounded durations](#zero-negative-and-unbounded-durations)
  - [Precision, strings, and invalid values](#precision-strings-and-invalid-values)
  - [Templates](#templates)
  - [Deprecation](#deprecation)
  - [Extenders and the 3rd-party ecosystem](#extenders-and-the-3rd-party-ecosystem)
  - [Out of scope](#out-of-scope)
- [Motivation](#motivation)
- [Rationale](#rationale)
  - [History](#history)
  - [Rejected designs](#rejected-designs)
- [Backwards Compatibility](#backwards-compatibility)
- [Open Questions](#open-questions)
- [Reference Implementation](#reference-implementation)
- [Copyright](#copyright)

## Abstract

Django accepts durations as a unitless primitive, most often second integers.
Furthermore, Django sometimes assigns special behavior to `None`, `0`, `-1` values.

Value ambiguity impacts code readability and requires users to hold or acquire
per-case knowledge of the individual values, units, and their meaning.

This DEP proposes four changes:

1. Every Django API and setting that accepts a duration must also accept
  `datetime.timedelta`.
2. `None` and `0` are replaced by named values or sentinels carrying their
   meanings, like: `IMMEDIATELY`, `DEFAULT`, `FOREVER`, or `BROWSER_SESSION`.
3. Using a numeral value emits a deprecation warning.
4. Two settings whose names contain a unit must be renamed because the value now
   carries the unit.

Django uses int or float durations internally only to interface with 3rd-party code,
apart from the exceptions in [The duration type](#the-duration-type) and
[Defaults](#defaults).

## Specification

This section describes the behavior after the deprecation period. [Backwards
Compatibility](#backwards-compatibility) describes the transition.

### The duration type

A duration is a `datetime.timedelta`. Where Django accepts a duration, Django accepts
a timedelta. Django also accepts a number of seconds until Django 2029, and emits a
warning for that number. [Deprecation](#deprecation) gives the details. The
[deprecation timeline][deprecation-timeline] lists 2029 as the removal release for
features deprecated in 6.2.

Durations that Django returns stay numbers. `SessionBase.get_expiry_age()`,
`SessionBase.get_session_cookie_age()`, `TimestampSigner.timestamp()`, and
`utils.cache.get_max_age()` are unchanged. [Out of scope](#out-of-scope) gives the
reason.

### Sentinels

A `timedelta` cannot state a duration without a limit. Django uses `None` for that case,
and the documentation gives the meaning in words: "never expire" and "unlimited".

`None` and `0` carry several meanings across the framework, and the value does not state
which one applies.

| Slot | `None` | `0` |
| --- | --- | --- |
| Cache timeout | Never expire | Expire at once |
| `CONN_MAX_AGE` | Unlimited | Close at the end of each request |
| `set_cookie(max_age=)` | Write no `max-age` attribute | Expire at once |
| `set_expiry()` | Use the global policy | Expire when the browser closes |
| `signing.loads(max_age=)` | No age check | An age of zero |

The same value means "expire at once" in a cache timeout and "expire when the browser
closes" in `set_expiry()`. A reader must know the surrounding API to read the value.

Django replaces both values in duration slots with four named values.

```python
# django/utils/duration.py

import datetime

DEFAULT = sentinel("DEFAULT")
FOREVER = sentinel("FOREVER")
BROWSER_SESSION = sentinel("BROWSER_SESSION")

IMMEDIATELY = datetime.timedelta(0)
```

`IMMEDIATELY` is a `timedelta`, not a sentinel. Zero is a duration that Django can
express, so the value needs a name and no special handling. Every backend already reads
it as zero, and `duration_to_seconds()` converts it to `0.0` with no branch.

`DEFAULT`, `FOREVER`, and `BROWSER_SESSION` are not durations and will be expressed
as a [`sentinel()`][pep-661] or their `object`-based predecessor. It
gives each value a `repr` of its own name, identity through `copy` and `pickle`, and a
static type of its own.

A sentinel is truthy. `None` is falsy, and so is `timedelta(0)`. A test such as
`if timeout:` therefore changes its result for `FOREVER`, and each such test must
become an explicit comparison, such as `if timeout is not BROWSER_SESSION:`.

| Name | Meaning | Earlier spelling |
| --- | --- | --- |
| `DEFAULT` | Use the configured default. | `None` in `set_expiry()` |
| `FOREVER` | No limit. Nothing expires. | `None` in a cache timeout, `CONN_MAX_AGE`, `EMAIL_TIMEOUT`, and `signing.loads(max_age=)` |
| `IMMEDIATELY` | A zero duration. The value expires at once. It is a `timedelta`, not a sentinel. | `0` in a cache timeout, `CONN_MAX_AGE`, and `set_cookie(max_age=)` |
| `BROWSER_SESSION` | The value ends when the browser session ends. | `None` in `set_cookie(max_age=)` and `LANGUAGE_COOKIE_AGE`, and `0` in `set_expiry()` |

Each name states the meaning at the call site.

- `cache.set("key", value, timeout=FOREVER)`
- `cache.set("key", value, timeout=IMMEDIATELY)`
- `CONN_MAX_AGE = FOREVER`
- `CACHES = {"default": {"TIMEOUT": FOREVER}}`
- `request.session.set_expiry(BROWSER_SESSION)`
- `request.session.set_expiry(DEFAULT)`
- `response.set_cookie("key", value, max_age=BROWSER_SESSION)`
- `LANGUAGE_COOKIE_AGE = BROWSER_SESSION`

`BROWSER_SESSION` unites two spellings that share one meaning. `set_expiry(0)` and
`set_cookie(max_age=None)` both produce a value that ends when the browser session
ends, and neither value states it.

`None` is not a duration. Where Django reads `None` as one today, Django emits a
`RemovedInDjango2029Warning` and applies the current meaning. Django rejects `None` in
2029 with a `TypeError`, so no later code depends on a meaning that the value does not
state.

A parameter whose default is `None` takes the name of the meaning it implements.
`signing.loads()` takes `max_age=FOREVER`, and `HttpResponse.set_cookie()` takes
`max_age=BROWSER_SESSION`. The default then states the behavior, and only an explicit
`None` emits a warning.

Rejected names:

- `NO_TIMEOUT`, `NO_EXPIRY`, and `NEVER_EXPIRES` state what is absent and cause
   awkward negations such as `timeout is not NO_TIMEOUT`.
- `INFINITE` and `INFINITY` name a mathematical limit. `timedelta` has no infinite
  value, and each backend maps the sentinel to a concrete value, such as `0` for
  memcached.
- `ETERNAL` is not technical English.
- `NOW` names a point in time. A point in time is a `datetime` value.
- `ALWAYS` names a frequency, not a duration.
- `ZERO` restates the number it replaces and states no outcome. `IMMEDIATELY` states
  the outcome, and it pairs with `FOREVER`.
- `SESSION` is ambiguous and collides with `django.contrib.sessions`.
- `NONE` reads as the builtin `None` and repeats the ambiguity it removes.

A computed duration can be zero, and Django cannot read the intent of a value it did not
write. `IMMEDIATELY` is the name for the zero that the author writes, and
`delete_cookie()` uses it in place of its current `max_age=0`.

### Backwards compatible normalization

One helper does the conversion: `duration_to_seconds()` in
`django/utils/duration.py`.

```python
# django/utils/duration.py

def duration_to_seconds(
    value: (
        datetime.timedelta
        | int
        | float
        | str
        | None
        | DEFAULT
        | FOREVER
        | BROWSER_SESSION
    ),
) -> float | str | None | DEFAULT | FOREVER | BROWSER_SESSION:
    """
    Return duration numeral in seconds.

    A ``datetime.timedelta`` is converted with ``total_seconds()``.
    A number, ``None``, and numeral strings are returned unchanged,
    with a ``RemovedInDjango2029Warning``.
    A sentinel is returned unchanged, without a warning.
    """
```

A value of another type is also returned unchanged. This rule keeps
`BaseCache.__init__()` working, because that method accepts a string through its
existing `int()` conversion.

Every API and setting in [The affected surface](#the-affected-surface) calls this
helper. As a result, Django has one conversion, one warning class, and one message.

The warning uses `skip_file_prefixes` with `django_file_prefixes()`. `EmailValidator`
in `django/core/validators.py` uses the same mechanism. Django's own code therefore
never emits this warning.

The helper replaces three inline `isinstance(value, datetime.timedelta)` tests. These
tests are in `django/core/signing.py`, `django/http/response.py`, and
`django/contrib/sessions/backends/base.py`.

### The affected surface

| Subsystem | Duration arguments and settings |
| --- | --- |
| Cache | `CACHES[alias]["TIMEOUT"]`, `cache.add()`, `cache.set()`, `cache.get_or_set()`, `cache.set_many()`, `cache.touch()`, `cache_page()`, the `{% cache %}` tag, `CACHE_MIDDLEWARE_SECONDS`, `utils.cache.patch_response_headers()`, `utils.cache.learn_cache_key()`, `BaseCache.get_backend_timeout()` |
| Sessions | `SESSION_COOKIE_AGE`, `SessionBase.set_expiry()` (already), `get_expiry_age(expiry=...)`, `get_expiry_date(expiry=...)` |
| Signing | `TimestampSigner.unsign(max_age=...)` (already), `signing.loads(max_age=...)`, `HttpRequest.get_signed_cookie(max_age=...)` |
| Cookies | `HttpResponse.set_cookie(max_age=...)` (already), `set_signed_cookie(max_age=...)` |
| CSRF | `CSRF_COOKIE_AGE` |
| i18n | `LANGUAGE_COOKIE_AGE` |
| Auth | `PASSWORD_RESET_TIMEOUT` |
| Database | `CONN_MAX_AGE`, for each connection alias |
| Mail | `EMAIL_TIMEOUT`, `smtp.EmailBackend(timeout=...)` |
| Security | `SECURE_HSTS_SECONDS` |

Django reads each setting through the same helper. As a result, an override in
`settings.py` emits a warning when Django uses the value. Django does not change the
`OPTIONS` of a database driver. [Out of scope](#out-of-scope) gives the reason.

### Defaults

Django owns these defaults. They become timedeltas, so that Django does not emit a
warning about its own code.

| Setting | Now | After |
| --- | --- | --- |
| `CACHES[alias]["TIMEOUT"]` / `BaseCache` default | `300` | `timedelta(minutes=5)` |
| `CACHE_MIDDLEWARE_SECONDS` | `600` | `timedelta(minutes=10)` |
| `SESSION_COOKIE_AGE` | `60 * 60 * 24 * 7 * 2` | `timedelta(weeks=2)` |
| `CSRF_COOKIE_AGE` | `60 * 60 * 24 * 7 * 52` | `timedelta(weeks=52)` |
| `PASSWORD_RESET_TIMEOUT` | `60 * 60 * 24 * 3` | `timedelta(days=3)` |
| `CONN_MAX_AGE` | `0` | `timedelta(0)` |
| `SECURE_HSTS_SECONDS` | `0` | `timedelta(0)` |
| `LANGUAGE_COOKIE_AGE`, `EMAIL_TIMEOUT` | `None` | unchanged |

The two settings with a unit in the name also change their name. [Names](#names) gives
the new names.

`BaseCache.default_timeout` stays a number of seconds. Django does not document this
attribute. Subclasses that read it keep their behavior. The memcached backend and the
Redis backend are two of them.

### Names

A name must not contain a unit of measure. The value carries the unit.

This rule has two directions. A new setting or argument must not repeat the unit,
such as `timeout_seconds=`. An existing name must lose the unit when the value
becomes a duration. During the deprecation period, functions may accept two
arguments. If both are set, Django will raise a `ValueError` to prevent conflicts.

Two Django settings contain a unit in the name. Both must be renamed.

| Old name | New name | Reason |
| --- | --- | --- |
| `CACHE_MIDDLEWARE_SECONDS` | `CACHE_MIDDLEWARE_TIMEOUT` | Django calls a cache duration a `TIMEOUT`: `CACHES[alias]["TIMEOUT"]`, `cache_page(timeout=...)`, and the `CacheMiddleware.cache_timeout` attribute. |
| `SECURE_HSTS_SECONDS` | `SECURE_HSTS_MAX_AGE` | The value is the `max-age` directive of the `Strict-Transport-Security` header, as [RFC 6797][rfc6797] defines it. |

The old name keeps its behavior during the deprecation period. `django/conf/__init__.py`
maps the old name to the new name. Django emits a `RemovedInDjango2029Warning` when a
project sets the old name. If a project sets the old name and the new name together,
Django raises `ImproperlyConfigured`.

`SecurityMiddleware` writes the HSTS value into a header. The middleware must convert
the duration to a whole number of seconds before it writes `max-age`. A `timedelta` in
a format string produces `max-age=365 days, 0:00:00`, which is not a valid header.

```python
# django/middleware/security.py

sts_header = "max-age=%d" % duration_to_seconds(self.sts_max_age)
```

### Zero, negative, and unbounded durations

Each named value keeps the meaning of the value it replaces.

- `IMMEDIATELY` means what `0` means today. For the cache, Django writes the key and
  the key expires at once. For `CONN_MAX_AGE`, Django closes the connection at the end
  of each request.
- `FOREVER` means what `None` means in these slots today. Cache keys never expire, and
  `CONN_MAX_AGE = FOREVER` is unlimited.
- A negative timedelta behaves like a negative number. Cache keys expire at once.

> [!CAUTION]
> Convert the duration before you compare it against zero. `timedelta(0) != 0` is
> `True`, because the types are different, and a sentinel equals neither value. Two
> cases exist today. The pooling tests in
> the PostgreSQL and Oracle backends compare `settings_dict.get("CONN_MAX_AGE", 0)`
> against `0`. The cache middleware compares `timeout` against `0`.

### Precision, strings, and invalid values

- `total_seconds()` returns a `float`. A `timedelta(milliseconds=500)` is `0.5`
  seconds. This precision is the precision of a `float` today.
- Django keeps the `int()` conversion for a setting that holds a number.
  `CACHES["TIMEOUT"] = 0.5` still becomes `0`.
- An invalid `TIMEOUT` still falls back to the default value. Django does not raise an
  error.
- Django keeps the current behavior for a string. `"300"` is valid, because Django
  applies `int()` to a setting, however a warning is emitted.
- The `{% cache %}` tag still rejects a value that is neither a duration nor
  convertible by `int()`. The tag can now resolve a timedelta from the context.

### Templates

Templates currently don't facilitate on-the-fly timedelta declarations.

The `{% cache %}` tag takes every argument by name. The fragment is `key=`, the
duration is `timeout=` or the `timedelta` keywords, and the varying arguments are
`vary_on=`. The existing `using="alias"` keyword does not change.

```html+django
{% cache key=sidebar days=2 %}
{% cache key=sidebar hours=1 minutes=30 %}
{% cache key=sidebar timeout=a_timedelta_context_var %}
{% cache key=sidebar days=2 vary_on=request.user.username %}
{# The positional form stays valid during the deprecation period. #}
{% cache 300 sidebar %}
```

The positional form emits a deprecation warning:

> Ambiguous positional cache durations are deprecated.
> Use the timeout=, days=, hours=, minutes=, and seconds= keywords instead.

### Deprecation

Deprecation messages must be helpful and include a concrete hint.

When a caller passes a number where Django expects a duration, Django emits
`django.utils.deprecation.RemovedInDjango2029Warning`. A message may read:

> Unit unaware numeral %(attr_name)r values are deprecated.
> Use `datetime.timedelta` instead.

A `None` in a duration slot emits the same class, with a message that names the
replacement sentinel:

> Ambiguous %(attr_name)r None values are deprecated.
> Use `django.utils.duration.FOREVER` instead.

Likewise:

> Ambiguous %(attr_name)r 0 values are deprecated.
> Use `django.utils.duration.IMMEDIATELY` instead.


### Extenders and the 3rd-party ecosystem

- A third-party cache backend that overrides `get_backend_timeout()` and omits the
  call to `super()` can receive a `timedelta` or a number during the deprecation
  period. After 2029, it receives a `timedelta` only. `duration_to_seconds()` is the
  supported way to convert the value, and Django must document it for that purpose.
- A `SessionBase` subclass that overrides `get_session_cookie_age()` keeps its
  behavior, because the return value is a number.
- Code that reads `settings.SESSION_COOKIE_AGE` and the other settings as numbers
  stops working when the defaults change type. [Backwards
  Compatibility](#backwards-compatibility) gives the details.

### Out of scope

These items are not part of this proposal.

- Django returns a number from `get_expiry_age()` and similar methods. A change of
  the return values is a second, larger change. [Open
  Questions](#open-questions) asks about it.
- Django passes the `OPTIONS` keys for a database driver, for example
  `connect_timeout`, to the driver. Django does not interpret these keys.
- A header keeps a non-negative integer value. `Cache-Control: max-age` is a
  delta-seconds value, as [RFC 9111][rfc9111] defines, and
  `Strict-Transport-Security: max-age` is the same. Django converts a duration to
  seconds when it writes the header, and `utils.cache.get_max_age()` keeps its
  behavior.
- `ASGIHandler.body_receive_timeout` and `DJANGO_WATCHMAN_TIMEOUT` are internal names,
  not public duration APIs.
- `django.utils.timezone.get_fixed_timezone()` takes a UTC offset, not a duration.
- `DurationField`, `parse_duration()`, `DjangoJSONEncoder`, and the ORM temporal
  expressions already accept a `timedelta`. This proposal does not change them.

## Motivation

The unit of a duration is not visible at the call site. `cache.set(key, value,
timeout=300)` does not say seconds. `SESSION_COOKIE_AGE = 1209600` does not say
seconds either. The documentation holds the only copy of the unit, and the reader has
usually left the documentation.

The convention does not travel to other libraries. Outside Django, the same bare
number is often a millisecond value. A signature and a setting name do not correct
that assumption.

`timedelta` is exact. It stores days, seconds, and microseconds. `timedelta(days=1)`
is one day in every file where it appears. `86400` is one day only for a reader who
already knows the unit.

## Rationale

### History

Django rejected this proposal once.

- [Trac #30144][trac-30144] asked for a timedelta in the cache timeout. Carlton
  Gibson closed the ticket as wontfix in 2019, and asked what was wrong with
  `timedelta(minutes=12).seconds`. Adam Johnson added two arguments. First, a function
  must accept one type, not two (TOOWTDI). Second, a number is more precise. A reader
  can understand one day as "until the end of today" instead of "in exactly 24 hours".
- The type answers the precision argument. A `timedelta` is exact, and
  `total_seconds()` returns an exact `float` for the ranges in this proposal.
- The deprecation answers the TOOWTDI argument. A number does not stay in Django.
- The decision changed after 2019. [Trac #21363][trac-21363] added a timedelta to
  `TimestampSigner.unsign(max_age=...)`. [Trac #33562][trac-33562] added a timedelta
  to `set_cookie(max_age=...)` and `set_signed_cookie(max_age=...)`.
  `SessionBase.set_expiry()` accepts a timedelta.
- The [new-features issue][new-features-156] asks the same question for the whole
  framework. It proposes the same shape as this DEP: accept the duration type and emit
  a warning for a number. The severity of the warning is a separate decision. This DEP
  selects the version with the removal release. [Open Questions](#open-questions)
  covers the stages of the change.

### Rejected designs

- Accept a `timedelta` and keep the number without a warning. This design is smaller
  and easier to merge. It keeps two conventions in the framework, and each new API
  must select one. The design does not correct the problem.
- Add `FOREVER` beside `None`, and keep both. Two spellings share one meaning, and
  `None` keeps the ambiguity that [Sentinels](#sentinels) removes. The reader still
  cannot tell "no limit" from "not set".
- Accept a `timedelta` and keep the defaults as numbers. This design protects
  arithmetic on the settings for a longer time. As a result, Django emits a warning
  about its own defaults on each request, or Django needs a suppression path for its
  own use.
- Add a unit suffix to each affected name and keep the old name
  (`SESSION_COOKIE_AGE_SECONDS`, `timeout_seconds=`). This design doubles the public
  surface, and the reader must select between two names for one value.
  [Names](#names) replaces a unit-bearing name instead of adding one.
- Change the documentation only. This option costs the least. Django used it since
  2019, and the framework now supports two conventions.
- Change the cache timeouts only, as [Trac #30144][trac-30144] proposed. This design
  corrects the most visible example and keeps the other settings as numbers. The
  inconsistency is not local to the cache, so the design is too narrow.
- Change the return values in the same DEP. This design is symmetric, and it is harder
  to review. Each caller of `get_expiry_age()` must change in the same release. The
  session middleware in Django is one caller.

## Backwards Compatibility

This DEP adds a deprecation. Nothing stops working immediately. Django accepts a
number, with a warning, until Django 2029.

The change of the default type is the sharp edge, not the deprecation.

> [!WARNING]
> Convert a setting before you do arithmetic on it. After the upgrade,
> `settings.SESSION_COOKIE_AGE`, `settings.CSRF_COOKIE_AGE`,
> `settings.PASSWORD_RESET_TIMEOUT`, `settings.CACHE_MIDDLEWARE_SECONDS`, and
> `settings.CONN_MAX_AGE` hold a `timedelta`, not an `int`. Code such as
> `settings.SESSION_COOKIE_AGE + 60` fails at that point, not at the removal.

The release notes must give the reader these aids.

- `timedelta(seconds=settings.SETTING)` restores the old expression where arithmetic
  is necessary.
- A third-party package that reads these settings needs a release that handles both
  types. During the deprecation period, `duration_to_seconds()` is the supported way
  to do this.
- Django's own code must change in the same release, because `tests/runtests.py`
  promotes these warnings to errors.
- A tool such as `django-upgrade` can rename the two settings in project code.

Other incompatibilities exist.

- A project that sets `CACHE_MIDDLEWARE_SECONDS` or `SECURE_HSTS_SECONDS` sees a
  warning at startup. A project that sets the old name and the new name together gets
  an `ImproperlyConfigured` error. Code that reads either old name must change after
  2029.
- `None` in a duration slot emits a warning, and Django rejects it in 2029. Code that
  calls `cache.set(key, value, timeout=None)` moves to `FOREVER`, and code that calls
  `set_expiry(None)` moves to `DEFAULT`.
- A third-party cache backend that overrides `get_backend_timeout()` without a call to
  `super()` sees a new type. Django documents this method as an override point, and
  the type changes. The release notes must describe the change.
- A project that runs its tests with `-W error` sees failures in its own call sites
  until it converts them.
- Django's system checks do not change. A setting that holds a number does not fail a
  check. Django emits the warning when it uses the value.

## Open Questions

These decisions belong to the review. The implementation owns the rest.

1. Django can change the default type now, or in 2029. A change now breaks arithmetic
   in third-party code immediately. A later change makes the deprecation period
   additive, and Django passes its own numeric defaults in the meantime.
2. Django can change the return values to durations, in this DEP or in a follow-up.
   `get_expiry_age()` is the first candidate, and the session middleware is its first
   caller.


## Reference Implementation

The [new-features issue][new-features-156] gives a sketch of the conversion helper.
Surfaces and APIs in this DEP come from the Django 6.2 development tree.

The concept of typed durations has been adopted in various language communities.
CodeAesthetic's ["Naming Things in Code"][naming-things-video] covers it.

## Copyright

This document has been placed in the public domain per the Creative Commons CC0
1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).

AI assistance was used for research and cataloguing the affected APIs of this proposal.
Used model: deepseek-v4.1-flash (MIT)

[new-features-156]: https://github.com/django/new-features/issues/156
[trac-30144]: https://code.djangoproject.com/ticket/30144
[trac-21363]: https://code.djangoproject.com/ticket/21363
[trac-33562]: https://code.djangoproject.com/ticket/33562
[deprecation-timeline]: https://docs.djangoproject.com/en/dev/internals/deprecation/
[rfc9111]: https://www.rfc-editor.org/rfc/rfc9111#section-5.2.2.1
[rfc6797]: https://www.rfc-editor.org/rfc/rfc6797#section-6.1.1
[pep-661]: https://peps.python.org/pep-0661/
[naming-things-video]: https://www.youtube.com/watch?v=-J3wNP6u5YU
