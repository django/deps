---
DEP: 0018
Author: Mike Edmunds
Implementation Team: Jacob Rief, Mike Edmunds
Shepherd: Natalia Bidart
Status: Draft
Type: Feature
Created: 2026‑02‑09
Last-Modified: 2026‑04‑21
---
# DEP 0018: Dictionary-based EMAIL_PROVIDERS settings

**Table of Contents**

- [Abstract](#abstract)
- [Motivation](#motivation)
- [Specification](#specification)
  - [`EMAIL_PROVIDERS` setting](#email_providers-setting)
  - [New exceptions](#new-exceptions)
  - [`using` argument to send functions](#using-argument-to-send-functions)
  - [`providers` factory](#providers-factory)
  - [Updates to built-in EmailBackend classes](#updates-to-built-in-emailbackend-classes)
  - [Related updates to other Django code](#related-updates-to-other-django-code)
- [Backwards compatibility](#backwards-compatibility)
  - [Deprecated email settings](#deprecated-email-settings)
  - [Settings compatibility](#settings-compatibility)
  - [Default provider compatibility](#default-provider-compatibility)
  - [`using` arg compatibility](#using-arg-compatibility)
  - [Testing outbox compatibility](#testing-outbox-compatibility)
  - [`fail_silently` sending option deprecated](#fail_silently-sending-option-deprecated)
  - [`get_connection()` deprecated](#get_connection-deprecated)
  - [`connection` arguments deprecated](#connection-arguments-deprecated)
  - [`auth_user` and `auth_password` deprecated](#auth_user-and-auth_password-deprecated)
  - [`AdminEmailHandler.email_backend` deprecated](#adminemailhandleremail_backend-deprecated)
  - [Third-party compatibility](#third-party-compatibility)
  - [Upgrading EmailBackend implementations](#upgrading-emailbackend-implementations)
  - [django-upgrade recommendations](#django-upgrade-recommendations)
- [Reference implementation](#reference-implementation)
- [Future work](#future-work)
  - [Future: System checks](#future-system-checks)
  - [Future: Password reset email provider](#future-password-reset-email-provider)
  - [Future: Provider-specific message defaults](#future-provider-specific-message-defaults)
  - [Future: Cached `providers`](#future-cached-providers)
- [Prior art](#prior-art)
- [History](#history)
- [AI disclosure](#ai-disclosure)
- [Copyright](#copyright)


## Abstract

This DEP proposes supporting multiple email provider configurations, via:
* a new dictionary-based `EMAIL_PROVIDERS` setting
* a new `mail.providers[alias]` factory
* adding `using=alias` args to email sending functions

This will align Django's email backend configuration with similar capabilities
in caches, databases, storages, and tasks.

In the process, we will deprecate and remove:
* most individual `EMAIL_*` settings
* the `connection` and `fail_silently` args to various email functions
* `mail.get_connection()`

**Status:** The feature was approved in 2024 through the older ticketing
process. This DEP is rapidly approaching a final draft. The
[implementation][PR #21052] is targeted to land in Django 6.1.


## Motivation

It's not uncommon for Django projects to use different email services—or
different configurations of the same email service—for different types of
email. For example:
* transactional notifications vs. bulk marketing emails
* internal operational reporting vs. email to end users
* different email services or hosts for specific geographic regions

Django's pluggable email backends and `mail.get_connection()` API do not
adequately support this need. And as a consequence, packages that send email
offer inconsistent (and sometimes complicated) extension points for overriding
the email configuration to use.

In addition, general reluctance to add new top-level settings has been a
blocking factor for some proposed features and fixes in Django's core email
handling. Moving EmailBackend-specific settings from the top level into
`EMAIL_PROVIDERS` OPTIONS dicts will allow that work to progress.


## Specification

Introducing dictionary-based EMAIL_PROVIDERS involves:
* a new `EMAIL_PROVIDERS` setting, replacing several existing ones.
* a new `using` argument to many django.core.mail APIs, identifying the
  provider alias to use for sending.
* a new `mail.providers[alias]` factory for getting EmailBackend instances.
* related updates to built-in EmailBackend classes, the testing mail outbox,
  and some other affected Django code.

This "specification" section defines the final,
post-deprecation-period behavior. A [later "compatibility"
section](#backwards-compatibility) details deprecations, transitional behavior
required to maintain compatibility during the deprecation period, and
considerations for third-party code.

### `EMAIL_PROVIDERS` setting

The new `EMAIL_PROVIDERS` setting is a dict mapping email provider "alias"
strings to EmailBackend import paths and options for those backends. Example:

```python
# settings.py

EMAIL_PROVIDERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "OPTIONS": {
            "host": "smtp-relay.gmail.com",
            "username": "app@corp.example.com",
            "password": env["GMAIL_APP_PASSWORD"],
            "timeout": 15,
            "use_tls": True,
        },
    },
    "notifications": {
        "BACKEND": "anymail.backends.mailtrap.EmailBackend",
        "OPTIONS": {
            "api_token": env["MAILTRAP_API_TOKEN"],
        },
    },
}
```

`EMAIL_PROVIDERS` replaces the `EMAIL_BACKEND` setting and all backend-specific
`EMAIL_*` settings. (See [*Deprecated email
settings*](#deprecated-email-settings).)

Each entry in `EMAIL_PROVIDERS` is a dict with two optional keys:
* `"BACKEND"` specifies the import path to an EmailBackend class, defaulting
  to Django's built-in SMTP EmailBackend
* `"OPTIONS"` is a dict with additional parameters to use when creating
  that backend instance

OPTIONS dict keys must be valid Python identifiers. The key `"alias"` is
reserved. Attempting to include `"alias"` in the OPTIONS dict will raise
`InvalidEmailProvider` when that provider is first used.

Aliases, BACKEND paths, and OPTIONS dict *keys* must be strings. (Lazy strings
are not supported. Individual backend implementations determine whether lazy
strings are allowed for OPTIONS *values.*)

Although strongly recommended, the `"default"` alias is not strictly required
in `EMAIL_PROVIDERS`. Django does not check for it on startup (but see
[*Future: System checks*](#future-system-checks)). If `"default"` is missing,
attempts to send mail using the default alias will fail with
`EmailProviderDoesNotExist`.

#### Default `EMAIL_PROVIDERS`

If settings.py does not include `EMAIL_PROVIDERS`, the default is that *no*
providers are defined:

```python
# django/conf/global_settings.py

EMAIL_PROVIDERS = {}
```

Attempts to send mail when no provider is defined will raise an
`EmailProviderDoesNotExist` error that "The email provider 'default' is not
configured."

This forces users who want to send email to decide how to configure it, and
issues a clear error message if sending is attempted in an unconfigured state.
It is a deliberate change from earlier Django releases, where attempting to
send email with the default (unconfigured SMTP) settings often resulted in a
confusing error like "ConnectionRefusedError: \[Errno 61] Connection refused."

During the deprecation period, `EMAIL_PROVIDERS` is *not* defined by default
(does not appear in global_settings.py). Before Django 7.0,
`django.conf.settings.EMAIL_PROVIDERS` exists only if the user opts into it by
defining `EMAIL_PROVIDERS` in their settings.py. This is important for
compatibility during the transition: see [*Settings
compatibility*](#settings-compatibility).


#### New project settings.py template

The settings.py template used for `django-admin startproject` is updated to
provision the *console* EmailBackend and to note that the setting must be
modified to enable sending email. Something like:

```python
# django/conf/project_template/project_name/settings.py-tpl

# Email providers
# https://docs.djangoproject.com/en/{{ docs_version }}/topics/email/

EMAIL_PROVIDERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}
```

Using the console backend in the new project template (but not the global
settings defaults):

* provides a useful default for development—one which is guaranteed not to
  raise cryptic errors (unlike a default SMTP backend when local SMTP service
  is not available).
* makes visible that emails will not be sent until the setting is changed
  (unlike a hidden global settings default to the console backend).
* preserves the useful behavior that an unconfigured (missing from settings.py)
  `EMAIL_PROVIDERS` setting is interpreted as "Django doesn't know how to send
  email"—and results in clear error messages if sending is attempted.
* during the deprecation period, prevents a confusing deprecation warning for
  newly created projects when `EMAIL_PROVIDERS` isn't defined (see [*Settings
  compatibility*](#settings-compatibility)).

### New exceptions

#### `InvalidEmailProvider`

The new `django.core.mail.InvalidEmailProvider` error is a subclass of
`ImproperlyConfigured`. It is raised to report problems in `EMAIL_PROVIDERS`
configuration.

(It is analagous to `InvalidCacheBackendError`, `InvalidStorageError`,
`InvalidTaskBackend`, and `InvalidTemplateEngineError`. Omitting "error" in the
name is consistent with `ImproperlyConfigured` and follows the lead of the most
recent addition, `InvalidTaskBackend`.)

#### `EmailProviderDoesNotExist`

The new `django.core.mail.EmailProviderDoesNotExist` error is a subclass of
`InvalidEmailProvider` and `KeyError`. It is raised *only* on attempts to use
an email provider alias that has not been defined in `EMAIL_PROVIDERS`.

This can be helpful for reusable libraries that want to send email when email
is configured but not raise errors when it isn't:

```python
try:
    # Mail admins (using the default email provider).
    mail_admins("subject", "message")
except EmailProviderDoesNotExist:
    # settings.py does not define a default email provider.
    pass
```

(The [deprecated `fail_silently`
option](#fail_silently-sending-option-deprecated) was often used for this
purpose, but had the undesirable side effect of also suppressing genuine
configuration and runtime errors.)


### `using` argument to send functions

The django.core.mail APIs which send email accept a new `using` keyword-only
argument which specifies the `EMAIL_PROVIDERS` alias to use for sending:

```pycon
>>> from django.core.mail import send_mail
>>> send_mail("subject", "body", "from", ["to"], using="notifications")
    #                                            ^^^^^^^^^^^^^^^^^^^^^
```

This applies to:
* `send_mail()`
* `send_mass_mail()`
* `mail_admins()`
* `mail_managers()`
* `EmailMessage.send()`

`using` is a string alias name, not an EmailBackend instance. (This mirrors the
`using` param in many database methods. It allows future provider-based
features, like [message defaults](#future-provider-specific-message-defaults),
that might not be possible directly from a backend instance.)

If `using` is omitted, the default email provider is used.

The `using` arg conceptually replaces the existing `connection` arg, which is
[deprecated](#connection-arguments-deprecated) as part of this proposal.
`using` is [mutually exclusive](#using-arg-compatibility) with `connection` and
all other sending options deprecated in this DEP.

`using` affects how a message is sent. It's an option to the APIs that
initiate sending, *not* APIs that construct a message to be sent later. (So
`using` is *not* an EmailMessage attribute or constructor option. If it were,
`providers[alias].send_messages([msg1, msg2])` would be ambiguous. See
[ticket-35864] for the equivalent problem with `connection`.)

[ticket-35864]: https://code.djangoproject.com/ticket/35864

### `providers` factory

`django.core.mail.providers` is a dict-like factory for getting fully
configured EmailBackend instances from provider aliases.

```pycon
>>> from django.core.mail import providers
>>> providers["default"]
<django.core.mail.backends.smtp.EmailBackend object ...>
>>> providers["notifications"]
<anymail.backends.mailtrap.EmailBackend object ...>
>>> providers["DEFault"]
Error: EmailProviderDoesNotExist("The email provider 'DEFault' is not configured.")
```

`providers` is meant to parallel `django.core.cache.caches`,
`django.core.files.storage.storages`, `django.core.tasks.task_backends` and
`django.db.connections`. It has this public API:

* `providers[alias]` (`__getitem__(alias)`) returns an EmailBackend instance
  configured from the matching key in `EMAIL_PROVIDERS`. Aliases are
  case-sensitive. Raises `EmailProviderDoesNotExist` for an unknown alias
  or `InvalidEmailProvider` for other configuration problems.

* `providers.default` is equivalent to `providers["default"]`
  (using the [`DEFAULT_EMAIL_PROVIDER_ALIAS`](#default_email_provider_alias)).

  This is django.core.mail's equivalent of the default `cache.cache`,
  `default_storage`, `default_task_backend`, and `db.connection`.
  (A module-level default property is not possible: Django's `ConnectionProxy`
  and `LazyObject` helpers require cacheable instances. See the next section.)

The `providers` factory also implements these mapping methods:

* `providers.get(alias, /, default=None)`
  is like `providers[alias]` but returns the `default` value if `alias` is
  not configured (is not a key of `EMAIL_PROVIDERS`).

* `providers.__contains__(alias)` returns `True` if `alias` is configured,
  `False` otherwise. This call will never initialize an EmailBackend instance
  (unlike `providers[alias]` or `providers.get(alias)`).

* `providers.__iter__()` returns an iterator over the keys of
  `EMAIL_PROVIDERS`.

`providers` is read-only. It does *not* support `__setitem__()` or
`__delitem__()`. (These might be added later, as part of a future [cached
providers](#future-cached-providers) feature.)


#### `providers` instances are *not* cached

`providers[alias]` and other accessors return a new EmailBackend instance
each time they are called:

```pycon
>>> providers["default"] is providers["default"]
False
>>> providers.default is providers.default
False
```

To ensure backwards compatibility, `providers` generally cannot cache and reuse
backend instances. (This differs from caches/storages/tasks/db.connections, all
of which provide instance caching.)

Historically, Django's mail-sending APIs have created an EmailBackend instance,
used it for a single `send_messages()` call, and then discarded it. Although
most backend implementations probably *do* support repeated `open()`/`close()`
cycles, this behavior has never been specified in Django's docs (or even
implicitly required in typical use). And even if a backend *does* technically
support reuse across multiple `send_messages()` calls, that may have different
behavior from creating a new instance. (For example, Django's file email
backend generates a new timestamped filename for each new instance.)

Some of Django's built-in backends *could* safely allow instance reuse, at
least within a single thread. Caching providers could be supported as a
separate [follow-on feature](#future-cached-providers).

#### `providers.create_connection()`

`providers` also has one internal method:

* `providers.create_connection(alias, /)`: Creates a new
  EmailBackend instance for alias, based on the `EMAIL_PROVIDERS` setting.

This method is used to implement the public API, backwards compatibility in
other django.core.mail APIs, and may be useful in test cases.

Roughly (ignoring detailed error handling and special cases for backwards
compatibility):

```python
# django/core/mail/__init__.py

class EmailProvidersHandler:
    def create_connection(self, alias, /):
        try:
            config = settings.EMAIL_PROVIDERS[alias]
        except KeyError:
            raise EmailProviderDoesNotExist(
                f"The email provider '{alias}' is not configured."
            ) from None
        options = config.get("OPTIONS", {})
        backend_path = config.get("BACKEND", DEFAULT_EMAIL_BACKEND)
        backend_class = import_string(backend_path)
        return backend_class(alias=alias, **options)
```

In addition to the OPTIONS from settings, `create_connection()` passes
`alias=alias` to the EmailBackend constructor. The backend can use this
argument to determine whether it is being initialized from EMAIL_PROVIDERS or
backwards compatibility code: see [*Upgrading EmailBackend
implementations*](#upgrading-emailbackend-implementations). (The name `alias`
is consistent with storages, db, and caches; see also
[django/new-features#95].)

In the initial implementation, there's no need to use `django.utils.
connection.BaseConnectionHandler` for `providers`. (That could [change
later](#future-cached-providers).)

During the deprecation period, the method's behavior is [modified
slightly](#default-provider-compatibility) to handle backwards compatibility
cases.

[django/new-features#95]: https://github.com/django/new-features/issues/95

#### `DEFAULT_EMAIL_PROVIDER_ALIAS`

`DEFAULT_EMAIL_PROVIDER_ALIAS = "default"` is a new, internal constant.
django.core.mail code should use it rather than the string literal `"default"`.

For brevity and clarity, this spec sometimes writes `"default"` where the
implementation would actually use `DEFAULT_EMAIL_PROVIDER_ALIAS`.

(`DEFAULT_EMAIL_PROVIDER_ALIAS` is *not* a setting and is not meant to be
translated or overridden. Compare `DEFAULT_STORAGE_ALIAS`,
`DEFAULT_TASK_BACKEND_ALIAS`, and similar constants for caches and DB.)


### Updates to built-in EmailBackend classes

In `django.core.mail.backends`:

* `base.BaseEmailBackend.__init__()` is updated to accept an `alias` arg
  (defaulting to `None`) and store its value on a new `alias` instance
  property.

  In addition, the `BaseEmailBackend` will report any unexpected `**kwargs` as
  unknown `EMAIL_PROVIDERS` OPTIONS with an `InvalidEmailProvider` error. This
  is meant to provide a more helpful error message than Python's default
  `TypeError` for unknown arguments.

* Django's built-in email backends are updated following the guidance for
  [upgrading third-party EmailBackend
  implementations](#upgrading-emailbackend-implementations) later in this
  document. For the console, file, and SMTP backends this will involve
  significant changes to initialization.

There are some additional compatibility changes related to [*`fail_silently` in
EmailBackend implementations*](#fail_silently-in-emailbackend-implementations).

#### SMTP host and port

The SMTP backend treats a few configuration OPTIONS differently from the
corresponding settings used in earlier releases:

* `"host"` is required. An `InvalidEmailProvider` exception is raised if host
  is missing from OPTIONS. (The earlier `EMAIL_HOST` default of "localhost"
  leads to confusing errors or lengthy timeouts when an SMTP server is not
  configured on the local machine.)

* `"port"` dynamically defaults to 25, 465, or 587 depending on the `"use_ssl"`
  and `"use_tls"` OPTIONS, so can be omitted unless a non-standard port is
  required.

These changes apply only when the SMTP backend is being initialized through
`EMAIL_PROVIDERS`. For compatibility, the old behavior remains when deprecated
settings are in use.

#### Locmem (testing outbox) `sent_using`

When placing copies of sent messages in the `mail.outbox` testing outbox, the
locmem backend adds a `sent_using` property set to its own alias. This helps
tests verify which email provider was used to send a particular message.


### Related updates to other Django code

#### Testing outbox

Django's [test runner temporarily replaces][testing-email] *all* defined
`EMAIL_PROVIDERS` with the locmem EmailBackend (testing outbox). The change
is made in `django.test.utils.setup_test_environment()` and restored in
`teardown_test_environment()`.

For the earlier settings example that defines "default" and "notifications"
providers, `setup_test_environment()` effectively substitutes:

```python
EMAIL_PROVIDERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.locmem.EmailBackend",
        # no "OPTIONS"
    },
    "notifications": {
        "BACKEND": "django.core.mail.backends.locmem.EmailBackend",
        # no "OPTIONS"
    },
}
```

This replicates the previous behavior that substituted `EMAIL_BACKEND =
"django.core.mail.backends.locmem.EmailBackend"` during tests. (Note that
behavior is retained in certain backwards compatibility scenarios: see
[*Testing outbox compatibility*](#testing-outbox-compatibility).)

[testing-email]: https://docs.djangoproject.com/en/6.0/topics/testing/tools/#topics-testing-email


#### `AdminEmailHandler`

There are two changes in Django's logging `AdminEmailHandler`:

1. `AdminEmailHandler` accepts a new `using` argument, an alias to an email
   provider. (This replaces the existing `email_backend` argument, which must be
   [deprecated](#adminemailhandleremail_backend-deprecated).) `using` defaults to
   `None`, which uses the default provider.

    ```python
    # settings.py

    LOGGING = {
        # ...
        "handlers": {
            "mail_admins": {
                "level": "ERROR",
                "class": "django.utils.log.AdminEmailHandler",
                "using": "admin",
            },
        },
        # ...
    }
    ```

2. `AdminEmailHandler.send_mail()` is updated to replace the
   [deprecated `fail_silently=True`](#fail_silently-sending-option-deprecated)
   with an `EmailProviderDoesNotExist` check. (This appears to best match the
   intent of the previous `fail_silently` usage. See related discussion in the
   deprecation section.)

This change also removes the undocumented `AdminEmailHandler.connection()`
method and its call to [deprecated
`get_connection()`](#get_connection-deprecated). Although an internal method,
`connection()` seems to be a deliberate extension point. As a courtesy to
subclasses that may have been using it, `AdminEmailHandler`'s constructor
should issue an error indicating `connection()` is no longer supported if it is
present.

For compatibility, these implementation specifics are modified during the
deprecation period. See [*`fail_silently`
compatibility*](#fail_silently-compatibility).

#### `BrokenLinkEmailsMiddleware`

The call to `mail_managers()` in Django's `BrokenLinkEmailsMiddleware` is
modified to replace [deprecated](#fail_silently-sending-option-deprecated)
`fail_silently` with an `EmailProviderDoesNotExist` check. The details are
similar to the second item in `AdminEmailHandler` above, and are similarly
modified during the deprecation period.


## Backwards compatibility

The dictionary-based `EMAIL_PROVIDERS` features will be introduced with a
standard deprecation period. (Assuming this feature lands in Django 6.1, the
deprecations listed here would be removed in Django 7.0.)

Some backwards compatibility behavior depends on which settings are defined.
There are three supported settings.py states, identified throughout this
section using the following shorthand:

* "Deprecated settings": settings.py defines at least one of the deprecated
  email settings (listed below), but not `EMAIL_PROVIDERS`.

* "Updated settings": settings.py defines `EMAIL_PROVIDERS`, but none of the
  deprecated email settings.

* "Default settings": neither `EMAIL_PROVIDERS` nor any deprecated email
  setting is defined in settings.py (so only Django's default global_settings
  apply).

During the deprecation period:

* Using `EMAIL_PROVIDERS` is opt-in. If `EMAIL_PROVIDERS` is not defined in
  settings.py, all deprecated settings and APIs continue to work as they
  did before (but issue deprecation warnings). However, once a project
  defines `EMAIL_PROVIDERS`, the deprecated email settings are no longer
  usable, and trying to mix them is an error.

* `providers.default` and similar references to the default email provider
  work regardless of which settings are defined. If `EMAIL_PROVIDERS` is not
  defined, the default email provider will return the default
  `mail.get_connection()` initialized from deprecated or default settings.
  This allows updated code (including Django itself) to switch to `providers`
  without worrying about which settings are in use.

* When `EMAIL_PROVIDERS` is defined, most uses of `mail.get_connection()` will
  return the default email provider (with a deprecation warning). This allows a
  project to update its own settings even if some external dependencies are
  still using `get_connection()`.

The discussion below details how this is achieved and covers several related
deprecations and compatibility concerns.


### Deprecated email settings

The following Django [email-related settings] are deprecated:

* `EMAIL_BACKEND`
* Settings for filebased EmailBackend
  * `EMAIL_FILE_PATH`
* Settings for smtp EmailBackend
  * `EMAIL_HOST`
  * `EMAIL_HOST_PASSWORD`
  * `EMAIL_HOST_USER`
  * `EMAIL_PORT`
  * `EMAIL_SSL_CERTFILE`
  * `EMAIL_SSL_KEYFILE`
  * `EMAIL_TIMEOUT`
  * `EMAIL_USE_SSL`
  * `EMAIL_USE_TLS`

They should be replaced with OPTIONS entries in the appropriate
`EMAIL_PROVIDERS` alias. (See [*django-upgrade
recommendations*](#django-upgrade-recommendations).)

During the deprecation period:

* Defining any of these deprecated settings (but not `EMAIL_PROVIDERS`)
  issues deprecation warnings when the settings module is initialized.

* Defining both `EMAIL_PROVIDERS` and any deprecated setting **is not
  supported** and raises an `ImproperlyConfigured` error preventing startup.
  This avoids ambiguities and conflicts between the two mechanisms.

  Projects using multiple email backends **cannot switch** to
  `EMAIL_PROVIDERS` until *all* backends used have been updated to support
  providers-based initialization. For example, a project using
  django-celery-email to wrap Django's SMTP EmailBackend cannot upgrade its
  settings to use `EMAIL_PROVIDERS` until django-celery-email supports
  `EMAIL_PROVIDERS` (even though Django's SMTP EmailBackend is provider-ready).

* When "deprecated settings" are in use, attempting to read *any* deprecated
  email setting (whether or not defined in settings.py) issues a deprecation
  warning and returns the setting value. This ensures warnings for third-party
  code that accesses deprecated settings, even if they aren't specifically
  defined in settings.py. (These warnings are suppressed during certain
  operations described later.)

  During the deprecation period, all deprecated email settings retain their
  default values from earlier releases (in Django's global_settings defaults).

* When "updated settings" are defined, Django behaves as though the deprecated
  email settings do not exist, ignoring their global_settings defaults. This
  is meant to prevent ambiguous mixed settings scenarios in code that borrows
  Django's email settings (such as third-party mail packages).

  With `EMAIL_PROVIDERS` defined, reading any deprecated settings **becomes an
  `AttributeError`** with a message that the setting is not available when
  `EMAIL_PROVIDERS` is defined—not just a deprecation warning. (An
  `AttributeError` is required for correctly handling `hasattr(settings, ...)`.
  After the deprecation period, this becomes Python's usual `AttributeError:
  'Settings' object has no attribute…`.)

  Similarly, with `EMAIL_PROVIDERS` defined, the deprecated email settings
  are omitted from `dir(settings)`.

  This behavior may impact newly created projects (which define
  `EMAIL_PROVIDERS`) if they try to use third-party packages still using the
  deprecated settings. Django's release notes or migration docs should
  specifically cover this situation and suggest replacing `EMAIL_PROVIDERS`
  with deprecated settings until upgraded dependencies are available.

* When "default settings" are in use (no specific email configuration in
  settings.py), the settings module issues a warning that the default email
  provider will change from SMTP to none after the deprecation period.
  Something like (exact wording TBD), "Django 7.0 will not have a default email
  provider. Define EMAIL_PROVIDERS in settings.py to continue using the SMTP
  EmailBackend."

  (If `EMAIL_BACKEND` or any other deprecated setting *is* defined in
  settings.py, the settings module instead warns that setting is deprecated,
  per the first rule in this section.)

[email-related settings]: https://docs.djangoproject.com/en/6.0/ref/settings/#email


#### Unchanged settings

Implementation of this feature does not affect any of these other
[email-related settings], because they are not used for constructing
EmailBackend instances:

* Settings for construction and serialization of EmailMessage objects
  * `DEFAULT_FROM_EMAIL`
  * `EMAIL_USE_LOCALTIME`
  * (A separate, future ticket might move these into `EMAIL_PROVIDERS`: see
    [*Provider-specific message
    defaults*](#future-provider-specific-message-defaults).)
* Settings used by `mail_admins()` and `mail_managers()`
  * `ADMINS`
  * `EMAIL_SUBJECT_PREFIX`
  * `MANAGERS`
  * `SERVER_EMAIL`


### Settings compatibility

During the deprecation period, the [default
`EMAIL_PROVIDERS`](#default-email_providers) setting specified earlier is *not*
defined in Django's global settings defaults.

This ensures projects with "default settings" run with the same (deprecated)
settings defaults as in earlier releases: `EMAIL_BACKEND` is set to Django's
SMTP backend with all its default options.

It also allows checking whether the user has opted into `EMAIL_PROVIDERS`
("updated settings") via `hasattr(django.conf.settings, "EMAIL_PROVIDERS")`.
(During the deprecation period, both Django and third-party code may need to
distinguish "updated settings" from default or deprecated settings. The
[`AdminEmailHandler.send_mail()` compatibility](#fail_silently-compatibility)
logic below includes a case where this is necessary.)


### Default provider compatibility

During the deprecation period, the behavior of
[`providers.create_connection()`](#providerscreate_connection) is modified to:

* Fall back to `mail.get_connection()` for the default email provider when
  `EMAIL_PROVIDERS` is not defined ("deprecated" or "default settings"). This
  allows using `providers.default` without worrying about which settings are
  defined. (Attempting to access any `providers[alias]` other than "default"
  still raises `EmailProviderDoesNotExist`.)

* Support constructing the default `EMAIL_PROVIDER` with additional keyword args
  when called from `get_connection()` in certain compatibility scenarios,
  [described below](#get_connection-deprecated). (To discourage misues,
  additional keyword args are accepted only via a scarily-named
  `_deprecated_kwargs` param, rather than generic variable `**kwargs`.)

In both cases, warnings for deprecated email settings and other features
deprecated in this DEP are suppressed while using those deprecated features to
implement this compatibility behavior.


### `using` arg compatibility

The new [`using` argument](#using-argument-to-send-functions) is incompatible
with sending options deprecated in this DEP. Providing both `using` and any of
these raises a `TypeError`:

* [deprecated `connection`](#connection-arguments-deprecated) arg or
  `EmailMessage` attribute
* [deprecated `fail_silently`](#fail_silently-sending-option-deprecated) arg
* [deprecated `auth_user` and
  `auth_password`](#auth_user-and-auth_password-deprecated) args


### Testing outbox compatibility

During the deprecation period, the [testing outbox](#testing-outbox)
behavior described earlier is modified to maintain compatibility with
deprecated settings.

When "deprecated settings" or "default settings" are in use,
`django.test.utils.setup_test_environment()` retains its previous behavior of
substituting `EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"`,
and `teardown_test_environment()` restores the original `EMAIL_BACKEND` (which
may be undefined). It *does not* create an `EMAIL_PROVIDERS` setting override,
which would conflict with the deprecated email settings.

The test runner setting `EMAIL_BACKEND` does not count as deprecated email
setting use, so should *not* issue a deprecation warning.

Messages in the test `mail.outbox` will have their `sent_using` properties set
to `None` when they are sent through an email backend initialized from "default
settings" or "deprecated settings."


### `fail_silently` sending option deprecated

The `fail_silently` send-time arg is deprecated and will be removed after the
deprecation period. Passing it to any of these django.core.mail functions
issues a deprecation warning:

* `send_mail()`
* `send_mass_mail()`
* `mail_admins()`
* `mail_managers()`
* `EmailMessage.send()`

Investigation of existing code using `fail_silently` suggests that, despite its
*actual* behavior, callers had several different interpretations of its
*expected* functionality. Calls with `fail_silently=True` should be updated
with one of these options, depending on the caller's intent:

* To send a message if email has been configured but avoid raising an error
  if it hasn't (e.g., in a reusable app), wrap the send call in `try:` /
  `except EmailProviderDoesNotExist: pass`.

* To ignore *all* exceptions (e.g., to avoid cascading failures in an error
  handler), wrap the send call in `try:` / `except Exception: pass`.

* To ignore only SMTP related errors (the prior `fail_silently` behavior when
  used with the SMTP EmailBackend), wrap the send call in `try` / `except
  OSError: pass`. Note that this ignores both transient network glitches *and*
  SMTP configuration problems (just like the prior behavior).

* To ignore end user typos in `to` addresses and other delivery problems,
  remove the `fail_silently` arg. Recipient errors are not generally detected
  at send time, so using `fail_silently` for this purpose doesn't accomplish
  anything and could mask other problems like configuration errors.

  (In some local-delivery configurations, SMTP servers *may* report recipient
  errors at send time. Intercept `SMTPRecipientsRefused` and/or
  `SMTPResponseException` with particular `smtp_code` values to detect those
  cases.)

* To create an email configuration that ignores certain backend-dependent
  errors and reuse it for multiple sending operations, define an alias in
  `EMAIL_PROVIDERS` with OPTIONS `"fail_silently": True`, and refer to that
  alias with `using` in the send call.

Calls with `fail_silently=False` should be updated to remove the
`fail_silently` arg, as that was the default.

#### Rationale for deprecating `fail_silently`

The `fail_silently` send-time arg as implemented in Django 6.0 is fundamentally
incompatible with this proposal. It is presented as an option that affects
individual send operations, but is implemented as EmailBackend configuration (a
backend `__init__()` param).

With `mail.providers[alias]`, there is no clean way to request `fail_silently`
for a particular send. (That would require something like
`mail.providers.get(alias, fail_silently)`, which doesn't follow the pattern
established by cache/db/storage/tasks and would complicate future provider
instance caching.)

Earlier DEP revisions considered several options for reworking `fail_silently`
to be compatible with this proposal, but investigation into current usage and
[discussion in the Django forum][forum-fail_silently] concluded that the
feature is:

* poorly understood by users (all the caller intents listed earlier have been
  observed in the wild).
* inadequately and inaccurately documented ([ticket-36907]).
* inconsistently implemented in third-party email backends.

Given the overall confusion about its behavior, the pragmatic choice seemed to
be removing `fail_silently` entirely and recommending specific replacements
(language features like `try`/`except`, granular exceptions like
`EmailProviderDoesNotExist`) for the various use cases.

[ticket-36907]: https://code.djangoproject.com/ticket/36907

#### `fail_silently` compatibility

Django's two internal uses of `fail_silently=True` will be replaced with an
`EmailProviderDoesNotExist` check. (See
[`AdminEmailHandler`](#adminemailhandler) and
[`BrokenLinkEmailsMiddleware`](#brokenlinkemailsmiddleware) earlier.)

During the deprecation period, `AdminEmailHandler` and
`BrokenLinkEmailsMiddleware` must ensure compatibility when "deprecated
settings" or "default settings" are in effect. In particular, when
`EMAIL_PROVIDERS` is not defined, the backends those handlers use to send mail
must be initialized with `fail_silently=True` to retain the behavior of the
earlier code. (This internal compatibility use of deprecated features must not
result in additional deprecation warnings.)

#### `fail_silently` in EmailBackend implementations

Although this DEP removes the `fail_silently` *argument to sending APIs*, it
takes no position on whether *EmailBackend* implementations should continue to
offer a mode that ignores some errors. Each EmailBackend decides for itself
whether to retain `fail_silently` capabilities (and, as before, exactly which
errors should be silenced).

`fail_silently` mode is available as a configuration option. (After the
deprecation period, this is the *only* way it will be available.)

```python
EMAIL_PROVIDERS = {
    "default": {
        ...
    },
    "unimportant": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "OPTIONS": {
            # We don't really care if this email gets sent or not.
            "fail_silently": True,
        },
    },
}
```

During the deprecation period, Django's built-in email backends must continue
to support `fail_silently` as they do now. Third-party backends can make their
own decisions.

Because `fail_silently` is no longer a universal requirement, support in
Django's `BaseEmailBackend` is being phased out:

* Backends that will continue supporting `fail_silently` should handle the
  constructor arg locally, rather than forwarding it to `BaseEmailBackend`.
* During the deprecation period, the `BaseEmailBackend` will issue a
  deprecation warning if given a `fail_silently` keyword arg (but will
  continue to set the backend's `fail_silently` attribute from it).
* Attempting to read a backend's `fail_silently` attribute issues a deprecation
  warning if the backend subclass has not specifically defined that attribute.
* After the deprecation period Django's `BaseEmailBackend` will no longer set a
  `fail_silently` attribute on the backend.

Related to this, the `BaseEmailBackend` handling for unknown `**kwargs`
described earlier in [*Updates to built-in EmailBackend
classes*](#updates-to-built-in-emailbackend-classes) is modified during the
deprecation period:

* The `InvalidEmailProvider` error for unknown `**kwargs` is raised only when
  "updated settings" are in use (the backend has been initialized with an
  `alias`).

* With "default settings" or "deprecated settings" (no `alias`), unknown
  `**kwargs` will issue a deprecation warning.

(See also [*Upgrading EmailBackend
implementations*](#upgrading-emailbackend-implementations).)

Three of Django's built-in EmailBackends have specific support for
`fail_silently` mode: the console, filebased, and SMTP backends. They will
follow the guidelines above. (Whether and when to remove that support is
outside the scope of this DEP. It's not required for any of the work here.)


### `get_connection()` deprecated

The `django.core.mail.get_connection()` function is deprecated.

There are three common use cases for `get_connection()`
([GitHub code search][get-connection-usage]):

1. `get_connection()` with no arguments, to create an instance of the
   default EmailBackend. This is typically to reuse a single connection
   across several send calls. (See [*Sending multiple
   emails*][sending-multiple-emails] and the [EmailBackend context manager
   example][email-context-manager] in Django's docs.)

   `get_connection()` with no arguments should be replaced with
   `providers.default`. (This could be [automated with
   django-upgrade](#django-upgrade-recommendations).)

   (Or it should be removed entirely if it is not being reused:
   `send_mail(..., connection=get_connection())` is equivalent to
   `send_mail(..., connection=None)` is equivalent to just `send_mail(...)`
   without the `connection` arg.)

2. `get_connection(arg1=..., arg2=...)` called with keyword arguments but
   no backend import path.

   The most common use case for this is with `fail_silently=True`. That should
   be replaced with code that achieves the caller's intent, as discussed under
   [*`fail_silently` deprecated*](#fail_silently-sending-option-deprecated)

   Other `get_connection()` calls with keyword args are much less common, and
   should be replaced by defining an `EMAIL_PROVIDERS` alias with the keyword
   options and then referring to it with `using="alias"` or
   `mail.providers["alias"]` wherever the connection had been used.

3. `get_connection("path.to.EmailBackend")` called with a backend import
   path (and perhaps additional kwargs), to create an instance of a specific
   EmailBackend. This may be used as a pre-`EMAIL_PROVIDERS` approach to having
   multiple providers and configurations (see, e.g.,
   [*Mixing email backends*][anymail-multiple-backends] in the third-party
   django-anymail docs). It's also used by "wrapper" email backends like
   django-celery-email and django-mailer.

   Calls with a backend import path should be replaced by defining an
   `EMAIL_PROVIDERS` alias for the desired BACKEND (and OPTIONS for any keyword
   args). Then substitute `using="alias"` or `mail.providers["alias"]` wherever
   the connection had been used.

During the deprecation period, the implementation of `get_connection(...)` is
modified to issue deprecation warnings, but to continue supporting the first
two use cases even if the updated `EMAIL_PROVIDERS` setting is defined:

* In all cases issue a deprecation warning, ideally mentioning the suggested
  replacement from above.

* If called with no arguments, return `providers.default`.

* If called with keyword arguments but no `backend` import path, return
  `providers.create_connection(DEFAULT_EMAIL_PROVIDER_ALIAS,
  _deprecated_kwargs=kwargs)`. This covers deprecated `fail_silently`,
  `auth_user` and `auth_password` args (see below), as well as other possible
  deprecated usage involving kwargs.

* If called with a backend import path:
  * With "deprecated settings" or "default settings" use the existing logic
    to construct and return a specific backend instance. The backend
    constructor must be called without an `alias` argument (*not* with
    `alias=None`), to ensure compatibility with third-party backends that may
    not support extra kwargs. Warnings for reading deprecated email settings
    should be suppressed while constructing the EmailBackend.
  * With "updated settings" raise a `RuntimeError` indicating
    `get_connection(backend)` is not compatible with `EMAIL_PROVIDERS`.

[get-connection-usage]: https://github.com/search?q=django.core.mail+AND+%22get_connection%28%22+AND+language%3APython+AND+NOT+path%3Adjango%2F&type=code
[sending-multiple-emails]: https://docs.djangoproject.com/en/6.0/topics/email/#sending-multiple-emails
[email-context-manager]: https://docs.djangoproject.com/en/6.0/topics/email/#email-backends
[anymail-multiple-backends]: https://anymail.dev/en/stable/tips/multiple_backends/


### `connection` arguments deprecated

The `connection` argument to all django.core.mail functions and the Django
`EmailMessage()` constructor is deprecated. Providing it issues a deprecation
warning.

Similarly, the `EmailMessage.connection` property (which can be set after
constructing a message) is deprecated. Attempting to set or get it issues a
deprecation warning.

Two related, undocumented behaviors are removed immediately in Django 6.1,
without deprecation:

* The undocumented `EmailMessage.get_connection()` method is no longer called
  and is removed. As a courtesy to subclasses that may have overridden it,
  `EmailMessage.send()` will raise an error if `get_connection()` is defined.

* `EmailMessage.send()` no longer sets the message's `connection` property to
  the connection actually used for sending. (This undocumented behavior was
  also unreliable, as it didn't apply when using `backend.send_messages()`.)
  `EmailMessage.send()` still *uses* a `connection` set *before* sending,
  but no longer sets that property as a side effect of sending.


### `auth_user` and `auth_password` deprecated

The `auth_user` and `auth_password` args to `send_mail()` and
`send_mass_mail()` are deprecated. They are incompatible with `mail.providers`
for the same reasons as `fail_silently`.

Using `auth_user` or `auth_password` issues a deprecation warning. They
should be moved to `"username"` and `"password"` OPTIONS in an appropriate
`EMAIL_PROVIDERS` alias, and the call should then be updated to use
`using="alias"`.


### `AdminEmailHandler.email_backend` deprecated

The dotted import path [`email_backend`
argument][AdminEmailHandler.email_backend]
to `django.utils.log.AdminEmailHandler` is deprecated. It should be replaced
by defining an alias in `EMAIL_PROVIDERS` and using the new
[`AdminEmailHandler.using` option](#adminemailhandlerusing).

[AdminEmailHandler.email_backend]: https://docs.djangoproject.com/en/6.0/ref/logging/#django.utils.log.AdminEmailHandler:~:text=email_backend%20argument


### Third-party compatibility

Throughout the deprecation period, existing third-party packages will continue
working with existing apps as they do today—unless and until the user opts into
`EMAIL_PROVIDERS` in their settings.py. (Using deprecated features will, of
course, result in deprecation warnings.)

Packages that implement EmailBackends may require updates to work with
`EMAIL_PROVIDERS`, covered [below](#upgrading-emailbackend-implementations).

Packages that send email by calling `django.core.mail` APIs *without* using the
`connection` or `fail_silently` args usually *don't* need updates. But they may
want to add a way to specify a `using` email provider alias for sending.
Django's own plans for a [password reset email
provider](#future-password-reset-email-provider) and
[`AdminEmailHandler.using` option](#adminemailhandler) offer examples.

Packages that use `fail_silently=True` should rework that code per the guidance
in [*`fail_silently` deprecated*](#fail_silently-sending-option-deprecated). In
many cases, either removing `fail_silently` altogether or replacing it with a
`EmailProviderDoesNotExist` check is appropriate.

Packages that use `get_connection()` should replace it with an updated
alternative as discussed in [*`get_connection()`
deprecated*](#get_connection-deprecated) above. If the package calls
`get_connection()` with a dotted import path, the replacement should use
`mail.providers[alias]` with a package-specific or user-configurable provider
alias instead.

For packages that support multiple Django versions, support for the features
and changes described here can be detected with `django.VERSION >= (6, 1)` or
`hasattr(django.core.mail, "providers")`.

To detect whether the user has opted into `EMAIL_PROVIDERS` (what the
[compatibility section](#backwards-compatibility) calls "updated settings"),
check `hasattr(django.conf.settings, "EMAIL_PROVIDERS")`.


### Upgrading EmailBackend implementations

Code that implements an EmailBackend may need to be updated for email
providers. To work correctly with `mail.providers` an EmailBackend
implementation:

1. Must accept and forward unknown `**kwargs` to superclass init. This lets the
   `BaseEmailBackend` handle the new `alias` argument and issue helpful errors
   for unknown OPTIONS.

   Any backend-specific keywords must be removed from `**kwargs` before passing
   to the superclass. The preferred way to do this is with explicit keyword
   parameters for all supported options.

   If the backend has a `fail_silently` arg, decide whether to keep it. If
   keeping it, handle it locally (don't pass it to the superclass). See
   [*`fail_silently` in EmailBackend
   implementations*](#fail_silently-in-emailbackend-implementations).

2. Must treat keyword arguments as overriding settings or default values. When
   initialized through `mail.providers`, the keyword args come from OPTIONS
   in the `EMAIL_PROVIDERS` setting, so should take precedence

   For required options, it's usually best to detect missing values and raise
   `InvalidEmailProvider`. (Defining a keyword param with no default also
   works, but results in a less helpful, generic `TypeError` from Python.)

   ❗️ Backend implementations **should not directly read**
   `settings.EMAIL_PROVIDERS[self.alias]["OPTIONS"]`. It seems tempting, but
   the OPTIONS are already in the `__init__()` args. Trying to read them
   directly from settings may break backwards compatibility or future features.

3. Should decide whether to continue supporting existing custom settings.

   If a backend *only* wants to allow configuration through `EMAIL_PROVIDERS`,
   existing custom settings can be deprecated or dropped. Some custom backends
   may want to retain existing settings as a common fallback when a value isn't
   provided in OPTIONS. (E.g., use `api_key` if in OPTIONS but default to
   `settings.CUSTOM_BACKEND_API_KEY` when not provided.)

   Django's own backends are switching to OPTIONS-only configuration after the
   deprecation period. During deprecation, they use settings values only when
   being initialized in compatibility mode (not through `mail.providers`). To
   differentiate, check `self.alias` after calling superclass init. If
   `self.alias is None`, compatibility applies; when `self.alias` is set the
   backend was initialized from `EMAIL_PROVIDERS` OPTIONS.

   For packages supporting multiple Django versions, either check
   `django.VERSION >= (6, 1)` or feature test for `hasattr(django.core.mail,
   "providers")` to determine if the email providers feature is available. And
   substitute `getattr(self, "alias", None)` for `self.alias` since it's not
   set in earlier Django versions.

4. Must not access Django's deprecated email settings when `EMAIL_PROVIDERS` is
   defined. Trying to read them will raise an `AttributeError`. This may affect
   custom email backends that borrow Django settings like `EMAIL_HOST`.

   A backend that wants to mimic Django's compatibility behavior should check
   `self.alias` as described in the previous item, and only access Django's
   deprecated email settings in compatibility mode (when `self.alias is None`).

Here's an example. Before migration, this EmailBackend for the hypothetical
Wheemail service gets a required WHEEMAIL_API_KEY and optional WHEEMAIL_REGION
from settings. It also looks for "debug" in `**kwargs` to enable extra logging:

```python
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend

class WheemailBackend(BaseEmailBackend):
    def __init__(self, api_key=None, region=None, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = api_key or getattr(settings, "WHEEMAIL_API_KEY", None)
        self.region = region or getattr(settings, "WHEEMAIL_REGION", "eu")
        self.debug = kwargs.get("debug", False)
        if not self.api_key:
            raise ImproperlyConfigured("Add WHEEMAIL_API_KEY to your settings")

    # ... other methods ...
```

To update it for `EMAIL_PROVIDERS`, maintaining pre-Django 6.1 compatibility
and deprecating the custom settings in Django 6.1 and later:

```python
import django.core.mail
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import InvalidEmailProvider
from django.core.mail.backends.base import BaseEmailBackend

class WheemailBackend(BaseEmailBackend):
    DEFAULT_REGION = "eu"

    # Forward unused **kwargs to BaseEmailBackend to initialize self.alias.
    # Handle fail_silently locally if keeping it (or remove it if not).
    def __init__(self, api_key=None, region=None, fail_silently=False, **kwargs):
        self.debug = kwargs.pop("debug", False)  # pop() to remove "debug" from kwargs
        super().__init__(**kwargs)  # don't pass fail_silently to base class
        self.fail_silently = fail_silently

        alias = getattr(self, "alias", None)  # or just self.alias for Django >= 6.1

        # Issue deprecation warnings/errors for custom settings (optional).
        if hasattr(settings, "WHEEMAIL_API_KEY") or hasattr(settings, "WHEEMAIL_REGION"):
            if alias is not None:
                # This can only occur on Django 6.1+ with EMAIL_PROVIDERS defined.
                raise ImproperlyConfigured(
                    "Don't mix WHEEMAIL_* settings with EMAIL_PROVIDERS"
                )
            elif hasattr(django.core.mail, "providers"):
                # Running on Django 6.1+.
                warnings.warn(
                    f"Replace WHEEMAIL_* settings with OPTIONS in EMAIL_PROVIDERS.",
                    DeprecationWarning
                )

        if alias is not None:
            # Being initialized in Django 6.1+ by mail.providers.
            # *All* options are in params. Don't use old settings.
            # (And don't access settings.EMAIL_PROVIDERS directly.)
            if not api_key:
                # It's helpful to identify the alias in the error message.
                raise InvalidEmailProvider(
                    "WheeMail requires 'api_key' in OPTIONS", alias=alias
                )
            self.api_key = api_key
            self.region = region or self.DEFAULT_REGION
        else:
            # Being initialized from deprecated settings or in an older Django version.
            # Use the original logic.
            self.api_key = api_key or getattr(settings, "WHEEMAIL_API_KEY", None)
            self.region = (
                region or getattr(settings, "WHEEMAIL_REGION", self.DEFAULT_REGION)
            )
            if not self.api_key:
                raise ImproperlyConfigured("Add WHEEMAIL_API_KEY to your settings")
```


#### Upgrading a wrapper EmailBackend

Packages like [django-celery-email] and [django-mailer] "wrap" some other
EmailBackend to add functionality, such as queuing and retry. They typically
have their own setting to specify an import path to the wrapped backend:

```python
# settings.py

# django-celery-email
EMAIL_BACKEND = "djcelery_email.backends.CeleryEmailBackend"
CELERY_EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# django-mailer
EMAIL_BACKEND = "mailer.backend.DbBackend"
MAILER_EMAIL_BACKEND = "anymail.backends.amazon_ses.EmailBackend"
```

The recommended upgrade for wrapper backends is:
* Follow the [instructions above](#upgrading-emailbackend-implementations),
  which apply generally to all EmailBackend implementations
* When initializing from updated settings (`alias is not None`):
  * Require a new `using` parameter that identifies the provider alias
    to wrap (and raise an error if it's missing)
  * Where the wrapper backend previously called
    `mail.get_connection(settings.WRAPPED_EMAIL_BACKEND)`,
    instead use `mail.providers[using]`

With that change, the updated settings from the django-mailer example above
would be:

```python
EMAIL_PROVIDERS = {
    "default": {
        "BACKEND": "mailer.backend.DbBackend",
        "OPTIONS": {
            # Replaces MAILER_EMAIL_BACKEND setting:
            "using": "wrapped",
        },
    },
    "wrapped": {
        "BACKEND": "anymail.backends.amazon_ses.EmailBackend",
    },
}
```

The indirection through `using` also allows specifying different instances
of the wrapper backend for different needs:

```python
EMAIL_PROVIDERS |= {
    # ... extending above example
    "notifications-eu": {
        "BACKEND": "mailer.backend.DbBackend",
        "OPTIONS": {
            "using": "wrapped-eu",
        },
    },
    "wrapped-eu": {
        "BACKEND": "anymail.backends.mailtrap.EmailBackend",
    },
}
```

If a wrapper is not designed to support multiple instances, it could prevent
that by requiring that `alias == "default"` in its own backend constructor. Or
instead of implementing a variable `using` option, it could send through a
specific fixed alias: e.g., `mail.providers["mailer-wrapped"]`.

[django-celery-email]: https://pypi.org/project/django-celery-email/
[django-mailer]: https://pypi.org/project/django-mailer/


### django-upgrade recommendations

In some cases, [django-upgrade] *may* be able to convert the deprecated
email settings to an `EMAIL_PROVIDERS` dict. For projects that use *only*
the default SMTP EmailBackend (and the standard test-time override),
django-upgrade could convert the related settings:

```python
EMAIL_PROVIDERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "OPTIONS": {
            "host": EMAIL_HOST,
            "port": EMAIL_PORT,
            "username": EMAIL_HOST_USER,
            "password": EMAIL_HOST_PASSWORD,
            "use_tls": EMAIL_USE_TLS,
            "use_ssl": EMAIL_USE_SSL,
            "timeout": EMAIL_TIMEOUT,
            "ssl_keyfile": EMAIL_SSL_KEYFILE,
            "ssl_certfile": EMAIL_SSL_CERTFILE,
        },
    },
}
```

If settings.py defines some other `EMAIL_BACKEND`, django-upgrade should not
convert anything.

Things get trickier if a project uses multiple email backends, e.g., via
`mail.get_connection()` or test-time `EMAIL_BACKEND` overrides. For example,
here's a settings file that strongly suggests the project is using multiple
email backends—but probably not in a way django-upgrade could detect or
properly convert. And upgrading just the `EMAIL_*` settings as above would
lead to errors when the other backends are used (due to the "no mixed
settings" rule):

```python
# Use Workspace email for most purposes.
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp-relay.gmail.com"
EMAIL_HOST_USER = env["GMAIL_APP_USER"]
EMAIL_HOST_PASSWORD = env["GMAIL_APP_PASSWORD"]

# For users in Europe, send through Mailtrap instead.
# See logic in project.utils.email_user().
ANYMAIL = {
    "MAILTRAP_API_TOKEN": env["MAILTRAP_API_TOKEN"],
}

# Some tests use filebased EmailBackend.
if sys.argv[1:2] == ["test"]:
    EMAIL_FILE_PATH = "tests/mail/__snapshot__"
```

(🤔 The more I think about this example, I'm not convinced django-upgrade can
*ever* safely upgrade existing settings, as it can't know the full set of
third-party settings that might conflict with the change, and it can't look
across the entire project to see if `get_connection()` is used to instantiate
non-default backends.)

Apart from settings, django-upgrade could also:
* convert calls to `mail.get_connection()` with no args to
  `mail.providers.default`
* remove unnecessary `fail_silently=False` args from calls to django.core.mail
  APIs
* remove unnecessary `connection=mail.get_connection()` args (where
  `get_connection()` is called with no args) from calls to django.core.mail
  APIs (but not `connection=foo` where `foo = mail.get_connection()` and is
  being used to share a single connection between calls)

In addition, a surprisingly large body of existing code and tutorials
(mis-)uses `EMAIL_HOST_USER` as the `from_email`:

```python
from django.conf import settings
from django.core.mail import send_mail

send_mail("subject", "message", settings.EMAIL_HOST_USER, ["to@example.com"])
```

A better way to handle this is setting `DEFAULT_FROM_EMAIL` and giving `None`
as the `from_email` when sending. django-upgrade operates on a single file at
a time. If it could somehow look across multiple files, it could update
settings.py to `DEFAULT_FROM_EMAIL = "old EMAIL_HOST_USER"` and then replace
`settings.EMAIL_HOST_USER` with `None` in sending calls.


[django-upgrade]: https://django-upgrade.readthedocs.io/


## Reference implementation

Django [PR #21052] provides a reference implementation.

[PR #21052]: https://github.com/django/django/pull/21052


## Future work

This section describes some **potential**, **future**, related features that
are *not* part of this proposal but may help inform some of the design
decisions here.

### Future: System checks

Two EMAIL_PROVIDERS-related system checks would be useful:

* Missing `"default"` alias in `EMAIL_PROVIDERS`
* The default email provider uses the console, dummy, or locmem EmailBackend,
  so email won't be sent (deployment check only—these options are valid in
  development configurations)

These are recommended as early follow-on work. (They are not strictly required
for this proposal and have been omitted here to control scope.)


### Future: Password reset email provider

Currently, using a different email provider for a django.contrib.auth password
reset email requires subclassing `PasswordResetForm` to override `send_mail()`.
Swapping in a different `using` (or `connection` in earlier Django versions)
isn't possible without also duplicating [all the email rendering
logic][PasswordResetForm.send_mail].

[PasswordResetForm.send_mail]: https://github.com/django/django/blob/7bc9d39fbdae6c09f630c6e5d51ea4ad2484fc46/django/contrib/auth/forms.py#L394-L421

This could be improved by refactoring `PasswordResetForm` with a new class
variable extension point for subclasses to override:

```python
# django/contrib/auth/forms.py
class PasswordResetForm:
    email_using = None

    def send_mail(self, ...):
        ...
        email_message = EmailMultiAlternatives(...)
        ...
        email_message.send(using=self.email_using)
```


### Future: Provider-specific message defaults

We could allow setting `EmailMessage` default values for each provider:

```python
EMAIL_PROVIDERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "DEFAULTS": {
            "from_email": "admin@example.com",
        },
    },
    "notifications": {
        "BACKEND": "django_ses.SESBackend",
        "OPTIONS": {
            "use_ses_v2": True,
        },
        "DEFAULTS": {
            "from_email": "notifications@example.com",
            "headers": {
                "Auto-Submitted": "auto-generated",
            },
        },
    },
}
```

The DEFAULTS would be used by the EmailMessage class (not EmailBackend
instances). This could replace the existing `DEFAULT_FROM_EMAIL` setting
(and with a little extra work, potentially `EMAIL_USE_LOCALTIME`,
`EMAIL_SUBJECT_PREFIX` and `SERVER_EMAIL`). DEFAULTS would also support a
contemplated `DEFAULT_EMAIL_HEADERS` capability ([ticket-35365#comment:7]).
The third-party django-anymail package has a similar feature: "[global send
defaults][anymail-send-defaults]."

(Defaults would be applied at send time, immediately before message
serialization, but once all EmailMessage properties have been finalized
and the provider alias is known.)

In anticipation of a feature like this, the current `EMAIL_PROVIDERS` proposal:
* Uses a nested `"OPTIONS"` dict rather than listing EmailBackend parameters
  at the same level as `"BACKEND"`.
* Uses a string `using="alias"` argument rather than an EmailBackend instance.

[ticket-35365#comment:7]: https://code.djangoproject.com/ticket/35365#comment:7
[anymail-send-defaults]: https://anymail.dev/en/stable/sending/anymail_additions/#global-send-defaults


### Future: Cached `providers`

Although EmailBackend instances are [not cacheable in
general](#providers-instances-are-not-cached), specific EmailBackend
implementations may be. For example, Django's SMTP EmailBackend is cacheable
and reusable within a single thread (though cannot be shared between threads as
currently implemented).

We could allow backends to opt into `mail.providers` caching via a future
`cacheable` class property:

```python
# django.core.mail.backends.smtp

class EmailBackend(BaseEmailBackend):
    cacheable = True
    ...
```

With this change, `mail.providers` would be implemented using
`django.utils.BaseConnectionHandler` (overriding `__getitem__()` to ensure
non-cacheable backends are always created anew).

```pycon
# Cacheable backends would be cached on providers:
>>> mail.providers["default"]
<django.core.mail.backends.smtp.EmailBackend object ...>
>>> mail.providers["default"].cacheable
True
>>> mail.providers["default"] is mail.providers["default"]
True

# But non-cacheable backends would not be cached:
>>> mail.providers["archive"]
<django.core.mail.backends.filebased.EmailBackend object ...>
>>> mail.providers["archive"].cacheable
False
>>> mail.providers["archive"] is mail.providers["archive"]
False
```

This change would also implement `__delitem__()` on `mail.providers` (or
possibly `__setitem__()` allowing only a `None` value), which would discard a
cached backend instance and force creation of a new one on the next access.


## Prior art

The django-lorien-common package implemented a similar
dictionary-based `EMAIL_CONNECTIONS` setting with a `get_custom_connection()`
function to create EmailBackend instances from it:
[django-lorien-common/common/mail.py].

[django-lorien-common/common/mail.py]: https://github.com/govtrack/django-lorien-common/blob/27241ff72536b442dfd64fad8589398b8a6e9f4d/common/mail.py


## History

This DEP is a bit unusual in that it postdates the approval of the feature it
proposes. See the links in this timeline for extensive earlier discussion:
* early 2022: [django-developers discussion]
* mid 2024 (?): Discussion at DjangoCon Europe sprints
* 2024-06-09: New feature [ticket-35514] opened and approved based on earlier
  discussion
* 2024-07-28: Jacob Rief opens Django [PR #18421] with an initial
  implementation
* 2024–2026: Iteration and discussion in the PR, which identifies a number of
  design issues
* 2026-02-09: This DEP created to help resolve issues raised by the PR and
  finalize API
* 2026-02-23–2026-03-12: Forum [discussion on
  `fail_silently`][forum-fail_silently] and other details

The DEP's revision history and additional commentary can be found in
django/deps [PR #105].

[ticket-35514]: https://code.djangoproject.com/ticket/35514
[PR #18421]: https://github.com/django/django/pull/18421
[django-developers discussion]: https://groups.google.com/g/django-developers/c/R8ebGynQjK0/m/Tu-o4mGeAQAJ
[PR #105]: https://github.com/django/deps/pull/105
[forum-fail_silently]: https://forum.djangoproject.com/t/changing-how-django-core-mail-handles-fail-silently/44278


## AI disclosure

AI assistance was used for:
* Investigating implications of caching EmailBackend instances (GPT-5.2)
* Analyzing impact of moving `fail_silently` into the sending APIs and out
  of the SMTP EmailBackend (Claude 4.6 Opus, which also first suggested this
  approach to resolving "the `fail_silently` problem" in an earlier draft)
* Proofreading and technical review (Claude 4.6 Opus; Gemini 3 Pro; GPT-5.2 and 5.4)


## Copyright

This document has been placed in the public domain per the Creative
Commons CC0 1.0 Universal license
(<http://creativecommons.org/publicdomain/zero/1.0/deed>).

(All DEPs must include this exact copyright statement.)
