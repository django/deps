---
DEP: XXXX
Author: Mike Edmunds
Implementation Team: Jacob Rief
Shepherd:
Status: Draft
Type: Feature
Created: 2026-02-09
Last-Modified: 2026-02-09
---
# DEP XXXX: Dictionary-based EMAIL_PROVIDERS settings

**Table of Contents**

- [Abstract](#abstract)
- [Specification](#specification)
  - [`EMAIL_PROVIDERS` setting](#email_providers-setting)
  - [`provider` argument to mail APIs](#provider-argument-to-mail-apis)
  - [`providers` factory](#providers-factory)
  - [Updates to built-in EmailBackend classes](#updates-to-built-in-emailbackend-classes)
  - [Related updates to other Django code](#related-updates-to-other-django-code)
- [Backwards compatibility](#backwards-compatibility)
  - [Deprecated email settings](#deprecated-email-settings)
  - [Default provider compatibility](#default-provider-compatibility)
  - [Testing outbox compatibility](#testing-outbox-compatibility)
  - [`get_connection()` deprecated](#get_connection-deprecated)
  - [The `fail_silently` problem](#the-fail_silently-problem)
  - [Other related deprecations](#other-related-deprecations)
- [Third-party packages](#third-party-packages)
  - [Upgrading packages that send email](#upgrading-packages-that-send-email)
  - [Upgrading EmailBackend implementations](#upgrading-emailbackend-implementations)
  - [Upgrading a wrapper EmailBackend](#upgrading-a-wrapper-emailbackend)
- [django-upgrade recommendations](#django-upgrade-recommendations)
- [Future work](#future-work)
  - [Future: Password reset email provider](#future-password-reset-email-provider)
  - [Future: Provider-specific message defaults](#future-provider-specific-message-defaults)
  - [Future: Cached `providers`](#future-cached-providers)
- [Motivation](#motivation)
- [Reference implementation](#reference-implementation)
- [AI disclosure](#ai-disclosure)
- [Copyright](#copyright)


## Abstract

Django [ticket-35514] will implement a dictionary-based `EMAIL_PROVIDERS` 
setting, similar to `CACHES`, `DATABASES`, and `STORAGES`. The ticket was 
approved following discussion on the django-developers list and at 
DjangoCon Europe 2024 sprints.

The purpose of this DEP is to facilitate discussion and decisions on the 
proposed API and related deprecations. **🤔 marks open questions.**

See also:
* The original [django-developers discussion] from 2022
* Discussion in [ticket-35514]
* Django [PR #18421] by Jacob Rief (which helped surface many of the issues 
  considered here)

[ticket-35514]: https://code.djangoproject.com/ticket/35514
[PR #18421]: https://github.com/django/django/pull/18421
[django-developers discussion]: https://groups.google.com/g/django-developers/c/R8ebGynQjK0/m/Tu-o4mGeAQAJ


## Specification

Introducing dictionary-based EMAIL_PROVIDERS involves:
* A new `EMAIL_PROVIDERS` setting, replacing several existing ones
* A new `provider` argument to many django.core.mail APIs, identifying the 
  provider alias to use
* A new `mail.providers[alias]` factory for getting EmailBackend instances
* Related updates to built-in EmailBackend classes, the testing mail outbox, 
  and some other affected Django code 

Plus a number of deprecations and recommendations for third-party code, 
covered separately in later sections.


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
            "user": "app@corp.example.com",
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
`EMAIL_*` settings. (See [*Deprecated email settings*](#deprecated-email-settings) later.)

Each entry in `EMAIL_PROVIDERS` is a dict with:
* a required `"BACKEND"` key with the import path to an EmailBackend class
  (🤔 should BACKEND be optional and default to smtp.EmailBackend?)
* an optional `"OPTIONS"` dict with additional parameters to use when creating
  that backend instance

Lazy strings are not supported for aliases or OPTIONS dict keys. (Individual 
backend implementations determine whether lazy strings are allowed for OPTIONS 
*values*.)

#### Default `EMAIL_PROVIDERS`

If settings.py does not include `EMAIL_PROVIDERS`, the default is to use 
Django's smtp.EmailBackend with its default options:

```python
EMAIL_PROVIDERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        # and no "OPTIONS". smtp.EmailBackend's own default options are:
        # "OPTIONS": {
        #     "host": "localhost",
        #     "port": 25,
        #     "username": "",
        #     "password": "",
        #     "use_tls": False,
        #     "use_ssl": False,
        #     "timeout": None,
        #     "ssl_keyfile": None,
        #     "ssl_certfile": None,
        # },
    },
}
```

This is a global_settings default. `EMAIL_PROVIDERS` is *not* included in 
the settings.py template used for startproject.

🤔 Should the settings.py `EMAIL_PROVIDERS` be shallow-merged with Django's 
global_settings default? That would ensure a `"default"` alias is always 
defined—otherwise omitting the `"default"` alias from `EMAIL_PROVIDERS` 
would mean calls to mail APIs that don't specify a provider would cause an 
error. Merged defaults also helps with some other open questions, like how 
to configure the [testing email provider override](#testing-outbox).

🤔 Or should defining `EMAIL_PROVIDERS` without a `"default"` alias be an 
`ImproperlyConfigured` error on settings initialization?


### `provider` argument to mail APIs

Several django.core.mail APIs accept a new `provider` keyword-only argument,
which specifies the `EMAIL_PROVIDERS` alias to use for sending:

```pycon
>>> from django.core.mail import send_mail
>>> send_mail("subject", "body", "from", ["to"], provider="notifications")
    #                                            ^^^^^^^^^^^^^^^^^^^^^^^^
```

This applies to:
* `send_mail()`
* `send_mass_mail()`
* `mail_admins()`
* `mail_managers()`
* `EmailMessage()` and `EmailMultiAlternatives()` constructors

Notes:
* The `provider` is a string alias name, not an EmailBackend instance. This is
  intentional, mirroring the `using` param in many database methods. It allows
  future provider-based features (like [message defaults](#future-provider-specific-message-defaults)) that wouldn't
  be possible directly from a backend instance.
  * 🤔 Naming? (`provider`? `alias`? `using`?)
* The existing `connection` arg is also still supported, and continues to 
  accept an EmailBackend instance (like the value of `mail.providers[alias]`,
  described in the next section).
  * 🤔 Or we could allow `provider` to take either an alias string or an
    EmailBackend instance, and deprecate `connection`: 
    `send_mail(..., provider=providers["notifications"])`.
* The `provider` and `connection` args are mutually exclusive. Passing both
  raises a `TypeError`.
* If neither `provider` nor `connection` is given, the default provider is
  used.
* The `auth_user` and `auth_password` args to `send_mail()` and 
  `send_mass_mail()` are not compatible with `provider`. Supplying both raises
  a `TypeError`. (They are already incompatible with the existing `connection`
  arg: [ticket-36894]. Also note that this proposal
  [deprecates these args](#auth_user-and-auth_password-deprecated).)
* Similarly, `fail_silently` and `provider` *might* be mutually exclusive: see 
  [*The `fail_silently` problem*](#the-fail_silently-problem).


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
Error: UnknownEmailProvider(...)
```

`providers` is meant to parallel `django.core.cache.caches`, 
`django.core.files.storage.storages` and `django.db.connections`. It has this
public API:

* `providers[alias]` (`__getitem__(alias)`) returns an EmailBackend instance
  configured from the matching key in `EMAIL_PROVIDERS`. Aliases are 
  case-sensitive. Raises `django.core.mail.UnknownEmailProvider` (a new
  subclass of `ImproperlyConfigured`) for an unknown alias. (🤔 Naming:
  `EmailProviderDoesNotExist`? `InvalidEmailProviderError`?)

* `providers.get(alias, default=None)` is like `providers[alias]`, but returns
  `default` rather than raising an error if alias is unknown. (See
  [*Upgrading packages that send email*](#upgrading-packages-that-send-email)
  below for a use case.)

* `providers.default` is equivalent to `providers["default"]`. (Or really,
  `providers[DEFAULT_EMAIL_PROVIDER_ALIAS]` where the internal constant
  `DEFAULT_EMAIL_PROVIDER_ALIAS = "default"`.)

  This is the django.core.mail equivalent to the default `cache`, 
  `default_storage` and (db) `connection`. (A module-level default 
  `provider` property is not possible: Django's `ConnectionProxy` helper 
  requires cacheable instances. See the next section.)

The `providers` factory does *not* support `__setitem__()`, `__delitem__()`,
or (at least initially) `__iter__()`.


#### `providers` instances are *not* cached

`providers[alias]` and other accessors return a new EmailBackend instance 
each time they are called:

```pycon
>>> providers["default"] is providers["default"]
False
>>> providers.default is providers.default
False
```

To ensure backwards compatibility, `providers` generally cannot cache and 
reuse backend instances. (This differs from caches/storages/db.connections, 
all of which provide instance caching.)

Historically, Django's mail-sending APIs have created an EmailBackend 
instance, used it for a single `send_messages()` call, and then discarded 
it. Although most backend implementations probably *do* support repeated 
`open()`/`close()` cycles, this behavior has never been specified in 
Django's docs (or even implicitly required in typical use). And even if a 
backend *does* technically support reuse across multiple `send_messages()` 
calls, that may have different behavior from creating a new instance. (For 
example, Django's filebased.EmailBackend generates a new timestamped 
filename for each new instance.)

Some of Django's built-in backends *could* safely allow instance reuse, at 
least within a single thread. Caching providers could be supported as a 
separate [follow-on feature](#future-cached-providers).


#### `providers.create_connection()`

`providers` also has one internal method:

* `providers.create_connection(alias, /, **kwargs)`: Creates a new 
  EmailBackend instance for alias, based on the `EMAIL_PROVIDERS` setting.

This method is used to implement the public API, backwards compatibility in 
other django.core.mail APIs, and may be useful in test cases.

Roughly (ignoring detailed error handling and special cases for backwards 
compatibility):

```python
class EmailProvidersHandler:
    def create_connection(self, alias, /, **kwargs):
        try:
            config = settings.EMAIL_PROVIDERS[alias]
        except KeyError:
            raise UnknownEmailProvider(alias) from None
        options = config.get("OPTIONS", {})
        backend_class = import_string(config["BACKEND"])
        return backend_class(alias=alias, **options, **kwargs)
```

Notes:

* In addition to the OPTIONS from settings, create_connection() passes 
  `alias=alias` to the EmailBackend constructor. The backend can use this 
  parameter to determine whether it is being initialized from EMAIL_PROVIDERS 
  or backwards compatibility code: see [*Upgrading EmailBackend 
  implementations*](#upgrading-emailbackend-implementations) later. (The name 
  `alias` is consistent with storages, db and caches; see also
  [django/new-features#95].)

* The variable `**kwargs` extend or override any OPTIONS from settings. 
  This mechanism is used *solely* for backwards compatibility, and it could 
  be removed at the end of the deprecation period. (See [`get_connection()` 
  deprecated](#get_connection-deprecated) and [*The `fail_silently` 
  problem*](#the-fail_silently-problem) in the backwards compatibility 
  section.)

* During the deprecation period, the behavior of `create_connection()` is 
  [modified slightly](#default-provider-compatibility) for the default 
  provider.

* In the initial implementation, there's no need to use `django.utils.
  connection.BaseConnectionHandler` for `providers`. (That could [change 
  later](#future-cached-providers).)

[django/new-features#95]: https://github.com/django/new-features/issues/95


### Updates to built-in EmailBackend classes

In `django.core.mail.backends`:

* `base.BaseEmailBackend.__init__()` is updated to accept an `alias` arg 
  (default to `None`) and store its value on a new `alias` instance 
  property. (For compatibility, BaseEmailBackend must continue to accept 
  and ignore all unknown kwargs.)

* The dummy, locmem (testing) and console email backends don't need to be 
  changed. (They forward all keyword args to the superclass constructor.)

  🤔 We might want to change them to explicit keyword args so that typos or 
  unsupported OPTIONS in settings.py cause errors, rather than being 
  swallowed silently.

* filebased.EmailBackend and smtp.EmailBackend are updated following the 
  guidance for [upgrading third-party EmailBackend 
  implementations](#upgrading-emailbackend-implementations) later in this
  document. This involves significant changes to backend initialization. Using
  our own recommendations ("dogfooding") helps ensure this proposal will be 
  workable for other Django packages.


### Related updates to other Django code

#### Testing outbox

Django’s [test runner temporarily replaces][testing-email] *all* defined 
`EMAIL_PROVIDERS` with the locmem.EmailBackend (testing outbox). The change 
is made in `django.test.utils.setup_test_environment()` and restored in 
`teardown_test_environment()`.

For the earlier settings example that defines "default" and "notifications" 
providers, `setup_test_environment()` substitutes:

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

🤔 Do we need some terse way to disable this (to use the real backends in 
test cases, e.g., for integration testing)? In earlier releases, a single 
`@override_settings(EMAIL_BACKEND="real.EmailBackend")` could achieve this. 
The equivalent now would require duplicating the entire original 
`EMAIL_PROVIDERS` dict in the test code, which is verbose and error-prone.

🤔 Should we instead allow a "test" provider alias which defaults to the 
locmem.EmailBackend? During testing, *all* defined provider aliases would 
resolve to `"test"`. This would allow users to easily substitute their own 
test outbox: e.g., a Mailtrap sandbox, or Django's filebased backend for 
snapshot testing. (We'd add "test" to Django's global defaults 
`EMAIL_PROVIDERS` and use the settings shallow merge approach mentioned 
earlier.)

🤔 Tests are likely to want to check which email provider was used to send a 
particular message in the outbox. (That might be a follow-on ticket to 
enhance the locmem backend.)

🤔 Does `mail.providers` need to monitor the `setting_changed` signal to 
catch the overrides? (Probably not, since we're not caching backend 
instances yet.)

[testing-email]: https://docs.djangoproject.com/en/6.0/topics/testing/tools/#topics-testing-email


#### `AdminEmailHandler.provider`

Django's logging `AdminEmailHandler` accepts a new `provider` argument, an 
alias to an email provider. It defaults to `None`, which uses the default 
provider.

```python
LOGGING = {
    # ...
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "provider": "admin",
        },
    },
    # ...
}
```

(This replaces the existing `email_backend` argument, which must be 
[deprecated](#adminemailhandleremail_backend-deprecated).)


## Backwards compatibility

The dictionary-based `EMAIL_PROVIDERS` features will be introduced with a 
standard deprecation period. (Assuming this feature lands in Django 6.1, 
the deprecations listed here would be removed in Django 7.0.)

Some backwards compatibility behavior depends on which settings are defined.
The descriptions below cover these cases:

* *Deprecated settings:* settings.py defines at least one of the deprecated 
  email settings (listed below), but not `EMAIL_PROVIDERS`

* *Updated settings:* settings.py defines `EMAIL_PROVIDERS`, but none of the 
  deprecated email settings

* *Default settings:* neither `EMAIL_PROVIDERS` nor any deprecated email 
  setting is defined in settings.py (so only Django's default global_settings
  apply)

During the deprecation period:

* Using `EMAIL_PROVIDERS` is opt-in. If `EMAIL_PROVIDERS` is not defined in 
  settings.py, all deprecated settings and APIs continue to work as they 
  did before (but issue deprecation warnings). However, once a project 
  defines `EMAIL_PROVIDERS`, the deprecated email settings are no longer 
  usable, and trying to mix them is an error.

* Code can use `django.core.mail.providers.default` (and similar references 
  to the default email provider) regardless of which settings are defined.

### Deprecated email settings

The following Django [email-related settings] are deprecated:

* `EMAIL_BACKEND`
* Settings for filebased.EmailBackend
  * `EMAIL_FILE_PATH`
* Settings for smtp.EmailBackend
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
recommendations*](#django-upgrade-recommendations) later.)

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
  `EMAIL_PROVIDERS`—even though Django's SMTP EmailBackend is provider-ready.

* When *deprecated settings* are in use, attempting to read *any* deprecated 
  email setting (whether or not defined in settings.py) issues a deprecation 
  warning and returns the setting value. This ensures warnings for third-party 
  code that uses deprecated settings, even if they aren't specifically defined 
  in settings.py. (These warnings are suppressed during certain operations 
  described later.)

  During the deprecation period, all deprecated email settings retain their 
  default values from earlier releases (in Django's global_settings defaults).

* With *updated settings,* reading most deprecated settings **becomes a hard 
  error,** not just a warning. Attempting to read any deprecated setting *other 
  than `EMAIL_BACKEND`* raises an `AttributeError` (🤔?) explaining the setting 
  is not available when `EMAIL_PROVIDERS` is defined. This prevents ambiguous 
  mixed settings scenarios in code that borrows Django's email settings (such
  as third-party mail packages).

* With either *updated settings* or *default settings,* reading
  `settings.EMAIL_BACKEND` issues a deprecation warning and returns the value
  of `EMAIL_PROVIDERS["default"]["BACKEND"]` (possibly from Django's
  global_settings defaults). This exception to the previous rule provides 
  compatibility for, e.g., third party libraries that validate certain 
  settings during system checks.


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


### Default provider compatibility

During the deprecation period and with any *deprecated settings* defined, 
the behavior of `providers.create_connection()` [described 
earlier](#providerscreate_connection) is modified to support constructing the 
default provider from the deprecated email settings. This allows updated 
code (including Django itself) to use `providers.default` without worrying 
about which settings are in use.

Ignoring error handling, the modification is roughly:

```python
class EmailProvidersHandler:
    def create_connection(self, alias, /, **kwargs):
        # RemovedInDjango70Warning
        if (
            alias == DEFAULT_EMAIL_PROVIDER_ALIAS
            and settings._any_deprecated_email_settings_are_defined()
        ):
            with settings._suppress_email_deprecation_warnings():
                backend_class = import_string(settings.EMAIL_BACKEND)
                return backend_class(**kwargs)  # no 'alias' arg!

        # Otherwise construct a backend from settings.EMAIL_PROVIDERS[alias]
        # as described earlier
        ...
```

Notes:

* In the compatibility branch, no `alias` argument is passed to the 
  EmailBackend constructor. This is the backend's cue to configure itself 
  from deprecated settings (plus any kwargs, just like in earlier Django 
  releases).

* Warnings for reading deprecated email settings are suppressed while 
  constructing the EmailBackend instance. This avoids a flood of confusing 
  deprecation messages while the backend constructor reads its deprecated 
  settings. (Django has already issued a deprecation warning on startup for 
  anything defined in settings.py.)

* When using *deprecated settings,* attempts to access any `providers[alias]`
  other than "default" raises `UnknownEmailProvider`. (This doesn't 
  require any extra code; it's a natural consequence of `EMAIL_PROVIDERS` 
  not being defined in the same settings.py as any deprecated settings.)

* (There are a few different ways to split the compatibility code between 
  `mail.providers.create_connection()` and `mail.get_connection()`. The 
  example code above is not a required implementation, but the resulting 
  behavior of the two APIs must be as described in this section and 
  [*`get_connection()` deprecated*](#get_connection-deprecated) below.)


### Testing outbox compatibility

During the deprecation period, the [testing outbox](#testing-outbox) 
behavior described earlier is modified to maintain compatibility with 
deprecated settings.

When any *deprecated settings* are defined, 
`django.test.utils.setup_test_environment()` retains its previous behavior of 
substituting `EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"`, 
and `teardown_test_environment()` restores the original `EMAIL_BACKEND` (which 
may be undefined). It *does not* create an `EMAIL_PROVIDERS` setting 
override, which would conflict with the deprecated email settings.

The test runner setting `EMAIL_BACKEND` does not count as deprecated email 
setting use, so should *not* issue a deprecation warning.


### `get_connection()` deprecated

The `django.core.mail.get_connection()` function is deprecated.

🤔 Deprecating `get_connection()` may be controversial. It seems required in 
the context of the other work here (and would be consistent with 
caches/db/storage). But it's used a lot 
([GitHub code search][get-connection-usage]) and can't entirely be handled 
by django-upgrade.

There are three common use cases for `get_connection()`:

1. `get_connection()` with no arguments, to create an instance of the 
   default EmailBackend. This is typically to reuse a single connection 
   across several send calls. (See [*Sending multiple 
   emails*][sending-multiple-emails] and the [EmailBackend context manager 
   example][email-context-manager] in Django's docs.)

   `get_connection()` with no arguments should be replaced with 
   `providers.default`.

   (Or it should be removed entirely if it is not being reused:
   `send_mail(..., connection=get_connection())` is equivalent to 
   `send_mail(..., connection=None)` is equivalent to just `send_mail(...)`
   without the `connection` arg.)

2. `get_connection(arg1=..., arg2=...)` called with keyword arguments but 
   no backend import path.

   The only common use case for this is with `fail_silently=True`, to 
   create an instance of the default backend with error reporting suppressed.
   See [*The `fail_silently` problem*](#the-fail_silently-problem) below.

   Other calls with keyword args are much less common, and should be replaced 
   with `providers["some-alias"]` and defining an `EMAIL_PROVIDERS` alias with 
   the keyword options.

3. `get_connection("path.to.EmailBackend")` called with a backend import 
   path (and perhaps additional kwargs), to create an instance of a specific
   EmailBackend. This may be used as a pre-`EMAIL_PROVIDERS` approach to using 
   mutiple providers and configuration (see, e.g.,
   [*Mixing email backends*][anymail-multiple-backends] in the third-party 
   django-anymail docs). It's also used by "wrapper" email backends like 
   django-celery-email and django-mailer.

   Calls with a backend import path should be replaced with 
   `providers["some-alias"]` and defining an `EMAIL_PROVIDERS` alias for the 
   desired connection configuration. Any kwargs should be moved to OPTIONS in
   the provider definition.

During the deprecation period, calling `get_connection(...)`:

* In all cases issues a deprecation warning, ideally mentioning the suggested 
  replacement.

* If called with no arguments, returns `providers.default`. (This could be
  combined with the following case.)

* If called with keyword arguments but no `backend` import path, returns 
  `providers.create_connection(DEFAULT_EMAIL_PROVIDER_ALIAS, **kwargs)`. This 
  covers `fail_silently`, the deprecated `auth_user` and `auth_password` params
  (see below), and other possible deprecated usage involving kwargs.

* If called with a backend import path:
  * With *deprecated settings* or *default settings,* uses the existing logic 
    to construct and return a specific backend instance. The backend 
    constructor must be called *without* an `alias` argument (not with 
    `alias=None`), to ensure compatibility with third-party backends that may 
    not support extra kwargs. Warnings for reading deprecated email settings
    should be suppressed while constructing the EmailBackend.
  * With *updated settings,* raises a `TypeError` (🤔?) indicating 
    `get_connection(backend)` is not compatible with `EMAIL_PROVIDERS`.

[get-connection-usage]: https://github.com/search?q=django.core.mail+AND+%22get_connection%28%22+AND+language%3APython+AND+NOT+path%3Adjango%2F&type=code
[sending-multiple-emails]: https://docs.djangoproject.com/en/6.0/topics/email/#sending-multiple-emails
[email-context-manager]: https://docs.djangoproject.com/en/6.0/topics/email/#email-backends
[anymail-multiple-backends]: https://anymail.dev/en/stable/tips/multiple_backends/


### The `fail_silently` problem

**Background:** Many django.core.mail APIs support a `fail_silently` boolean 
arg which suppresses some sending errors. Although the docs are a bit vague 
([ticket-36907]), the intended behavior seems to be ignoring transient network
errors that are common with email. The exact interpretation of `fail_silently` 
is up to each EmailBackend, but it typically *doesn't* block errors in 
configuration or message serialization (content).

One use case for `fail_silently` is with email as an error reporting 
mechanism, to avoid cascading failures. In fact, that's the *only* way 
Django's own code uses it, in calls to `mail_admins()` and `mail_managers()` 
from the logging `AdminEmailHandler` and `BrokenLinkEmailMiddleware`.

**Problem:** Although `fail_silently=True` is described and used as a modifier 
to the *sending* process, it's implemented as an EmailBackend *configuration* 
option (an instance constructor arg). That distinction hasn't mattered in the
past, but it doesn't work with an `EMAIL_PROVIDERS` setting that defines the 
full set of available configurations.

A sending API with `alias` and `fail_silently` args needs a way to say, "I 
want the usual `providers[alias]`, except just for now let's pretend its 
OPTIONS had included `"fail_silently": True`." And that requires some sort 
of special-case handling in the `providers` code—or forbidding that case.

(Django's existing `connection` args are already incompatible with 
`fail_silently` for the same reason: you can't retroactively modify an 
EmailBackend instance. See [ticket-36894].)

🤔 Some options:

1. Deprecate `fail_silently` as an API arg, and require that it be specified
   only in settings OPTIONS. Sending APIs that want to fail silently must accept 
   a provider alias, and callers must know to pass an alias where 
   `fail_silently` is set.

    ```python
    EMAIL_PROVIDERS = {
       "default": { ... },
       "admin": {
           "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
           "OPTIONS": {
               "fail_silently": True,
           },
       },
    }
    ```

   Pros: Goes all-in on `EMAIL_PROVIDERS`.

   Cons: Non-trivial upgrade for anyone using `fail_silently` args—including 
   Django's own usage in logging and middleware. Do we introduce automatic 
   "admin" and "managers" provider aliases for `mail_admins()` and 
   `mail_managers()` that magically extend "default"?

2. Change `fail_silently` from an EmailBackend constructor param to a 
   send-time param: `EmailBackend.send_messages(..., fail_silently)` (and 
   maybe also `EmailBackend.open(fail_silently)`).

   Pros: Matches how `fail_silently` is documented and used.

   Cons: Far-reaching change with complicated deprecation process. (I'm not 
   entirely sure how to do it.) If `open()` is affected, wouldn't work with 
   using a provider (backend instance) as a context manager.

3. Remove `fail_silently` from the EmailBackend implementations entirely, and
   instead implement it in `EmailMessage.send()` and `mail.send_mass_mail()`
   by wrapping `connection.send_messages()` in a broad try/catch.

   Pros: Matches how `fail_silently` is documented and used. 
   Straightforward implementation.

   Cons: Changes the semantics of `fail_silently` significantly: would 
   ignore *all* errors, not just ones deemed ignorable by the backend 
   implementor (though this might better match users' expectations).
   All other code that calls `EmailBackend.send_messages()` directly
   and wants `fail_silently` behavior would need to replicate the try/catch 
   wrapper. (Not sure how we handle that deprecation.)

4. Expose a separate `providers` API for getting an alias with `fail_silently` 
   set True: `providers.silent[alias]` (?).

   Callers would use something like 
   `connection=providers.silent[alias] if fail_silently else providers[alias]`.

   Pros: Allows (future) provider instance caching. Doesn't require 
   maintaining arbitrary `**kwargs` overrides in public `providers` API.

   Cons: Feels a little weird. Doesn't support defaulting `fail_silently=True`
   and overriding to `False` (which I'm not convinced is used anywhere now, 
   but is technically supported by the existing code). Do we have to mirror 
   other public APIs, like `providers.get()`: `providers.get_silent()`?

5. In the existing `providers` APIs, support a virtual `<alias>:silent` option
   for any defined alias: `providers["notifications:silent"]` is the same 
   as `providers["notifications"]` but with `{"fail_silently": True}` merged 
   into `EMAIL_PROVIDERS["notifications"]["OPTIONS"]`.

   Pros: Same as option 4.

   Cons: Same as option 4, but maybe feels a little less weird, and doesn't 
   require additional `providers` APIs.

6. Expose and maintain `create_connection()` with `**kwargs` (or at least a 
   `fail_silently` arg).

   Pros: Relatively straightforward to implement.

   Cons: Exposes an API other connection managers treat as internal. Can't 
   support provider instance caching. (And would likely encourage 
   `providers.create_connection(alias, fail_silently=fail_silently)` rather 
   than the cacheable `providers[alias]` even when `fail_silently` is False.) 
   Essentially reintroduces the deprecated `get_connection()` function 
   under a new name.

7. 🤔 Something else? (I'm not really thrilled with any of these.)

[ticket-36894]: https://code.djangoproject.com/ticket/36894
[ticket-36907]: https://code.djangoproject.com/ticket/36907


### Other related deprecations

#### `auth_user` and `auth_password` deprecated

The `auth_user` and `auth_password` args to `send_mail()` and 
`send_mass_mail()` are deprecated. They are incompatible with an explicit 
`provider` alias, and they require extra code in
`providers.create_connection()` (which we'd like to remove after the
deprecation period).

Using `auth_user` or `auth_password` issues a deprecation warning. They 
should be moved to `"username"` and `"password"` OPTIONS in an appropriate 
`EMAIL_PROVIDERS` alias, and the call should then be updated to use 
`provider="alias"`.

#### `AdminEmailHandler.email_backend` deprecated

The dotted import path [`email_backend`argument][AdminEmailHandler.email_backend]
to `django.utils.log.AdminEmailHandler` is deprecated. It should be replaced 
by defining an alias in `EMAIL_PROVIDERS` and using the new 
[`AdminEmailHandler.provider` option](#adminemailhandlerprovider).

[AdminEmailHandler.email_backend]: https://docs.djangoproject.com/en/6.0/ref/logging/#django.utils.log.AdminEmailHandler:~:text=email_backend%20argument


## Third-party packages

This section offers upgrade guidance for third-party packages that implement
Django mail-related features.

In all cases, existing packages will continue working as they do today 
throughout the deprecation period. (Using deprecated features will, of 
course, result in deprecation warnings.)

### Upgrading packages that send email

Packages that send email by calling `django.core.mail` APIs *without* using 
the `connection` or `fail_silently` args usually don't need updates, but may 
want to consider allowing purpose-specific provider aliases as described here.

Packages that use `get_connection()` should replace it with an updated 
alternative as discussed in [*`get_connection()`
deprecated*](#get_connection-deprecated) above. If the package calls 
`get_connection()` with a dotted import path, the replacement should use 
`mail.providers[alias]` with a package-specific or user-configurable provider 
alias instead. For packages that support multiple Django versions, this may 
require branching on `django.VERSION >= (7, 0)` or 
`hasattr(django.core.mail, "providers")` during the deprecation period.

As an example, `django-allauth` [sends email][allauth-email] confirmation
messages.

* Allauth's [`DefaultAccountAdapter.send_mail()`][allauth-send_mail] *does not*
  use `connection` or `fail_silently`, so will continue working with no changes
  or deprecation warnings. Mail will be sent using the default email provider,
  and users can subclass `DefaultAccountAdapter` to override this as described
  in Allauth's docs. No work is necessary.

* However, if Allauth wanted to allow a user-selectable email provider without
  subclassing, it could introduce a new setting 
  (`ALLAUTH_EMAIL_PROVIDER = "alias"`).

* Or Allauth could look for a known provider alias, which avoids creating new
  settings. For example, it could try both `"allauth"` (package specific) and
  `"email-confirmation"` (descriptive role) aliases before falling back to the
  default provider:

    ```python
    # allauth/account/adapter.py
    from django.core import mail

    class DefaultAccountAdapter:
        def send_mail(self, ...):
            # ...
            msg = self.render_mail(...)
            try:
                # Django 7.0 or later.
                connection = (
                    mail.providers.get("allauth")
                    or mail.providers.get("email-confirmation")
                    or mail.providers.default
                )
            except AttributeError:
                # Earlier Django versions didn't support mail.providers.
                connection = mail.get_connection()
            connection.send_messages([msg])
    ```

🤔 If we want to encourage this approach, perhaps we should offer a helper 
API? `mail.providers.resolve("allauth", "email-confirmation")` could return 
the first defined provider instance or `providers.default` if none are defined.

[allauth-email]: https://docs.allauth.org/en/latest/common/email.html
[allauth-send_mail]: https://codeberg.org/allauth/django-allauth/src/commit/8a4b13f0d878435b8a138e4f030bb2eb63340194/allauth/account/adapter.py#L212-L221


### Upgrading EmailBackend implementations

Code that implements an EmailBackend with any configurable options almost 
always needs to be updated for `EMAIL_PROVIDERS`. The approach here is 
meant to work for third-party backends, first-party backends directly in a 
project, and Django's own built-in email backends.

To support `EMAIL_PROVIDERS`, an EmailBackend implementation should:

1. Accept a new `alias` keyword arg, defaulting to `None`. Forward it to 
   superclass init, which will result in `self.alias` set to either an 
   `EMAIL_PROVIDERS` alias string or `None`. (Or just accept and forward all 
   `**kwargs`. But **explicit keyword params are preferred,** to avoid silently
   swallowing typos in the settings OPTIONS dict.)

2. Optionally issue deprecation warnings for settings that should be moved into
   `EMAIL_PROVIDERS` OPTIONS. And optionally raise an error if deprecated
   settings are being used alongside `EMAIL_PROVIDERS` (which can be detected
   by `alias is not None`).

   If the package supports multiple Django versions, only warn on Django 7.0 or
   later. Some packages might prefer to handle settings checks elsewhere, such
   as using Django's system check framework. (For Django's built-in
   EmailBackends, these warnings and errors are all implemented in Django's
   settings module rather than in the individual backends.)

3. When `alias is not None`, the backend is being initialized from updated
   `EMAIL_PROVIDERS` settings via `providers.create_connection()`. The provided
   keyword args include all OPTIONS from the settings. The backend should
   initialize and validate strictly from those args, without checking any
   settings. (`alias` will be set only in Django 7.0 or later, so there's no
   need to guard it in packages supporting multiple versions.)

4. Or if `alias is None`, the backend is being initalized in deprecated
   compatibility mode (or in a version of Django before 7.0). The backend
   should use its original logic, including reading any top-level settings.

❗️ Backend implementations **should not directly read**
`settings.EMAIL_PROVIDERS[alias]["OPTIONS"]`. It seems tempting, but the
OPTIONS are already in the `__init__()` args. Trying to read them directly
from settings may break backwards compatibility or future features. 

A good rule of thumb is to use `alias` *only* in error messages (to identify
the offending `EMAIL_PROVIDERS` entry) or to distinguish updated from
deprecated initialization (by checking for `None`). Any other use of `alias` is
likely problematic.

(🤔 Maybe Django should actively prevent misuse by blocking access to 
`settings.EMAIL_PROVIDERS` while `providers.create_connection()` is 
initializing the backend instance?)

Here's an example. This EmailBackend for the hypothetical Wheemail service 
gets a required WHEEMAIL_API_KEY and optional WHEEMAIL_REGION from settings:

```python
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend

class WheemailBackend(BaseEmailBackend):
    def __init__(self, api_key=None, region=None, fail_silently=False):
        super().__init__(fail_silently=fail_silently)
        self.api_key = api_key or getattr(settings, "WHEEMAIL_API_KEY", None)
        self.region = region or getattr(settings, "WHEEMAIL_REGION", "eu")
        if not self.api_key:
            raise ImproperlyConfigured("Add WHEEMAIL_API_KEY to your settings")

    # ... other methods ...
```

To update it for `EMAIL_PROVIDERS` (maintaining pre-Django 7.0 compatibility):

```python
class WheemailBackend(BaseEmailBackend):
    DEFAULT_REGION = "eu"

    # 1. Add alias=None and forward it to BaseEmailBackend to initialize self.alias.
    def __init__(self, api_key=None, region=None, alias=None, fail_silently=False):
        super().__init__(alias=alias, fail_silently=fail_silently)

        # 2. Issue warnings/errors (optional).
        if hasattr(settings, "WHEEMAIL_API_KEY") or hasattr(settings, "WHEEMAIL_REGION"):
            if alias is not None:
                # This can only occur on Django 7.0+ with EMAIL_PROVIDERS defined.
                raise ImproperlyConfigured("Don't mix WHEEMAIL_* settings with EMAIL_PROVIDERS")
            elif django.VERSION >= (7, 0):
                warnings.warn(
                    "Replace WHEEMAIL_* settings with EMAIL_PROVIDERS[alias]['OPTIONS'].",
                    DeprecationWarning)

        if alias is not None:
            # 3. Being initialized in Django 7.0+ by providers.create_connection() with
            #    updated settings. *All* options are in params. Don't use old settings.
            #    (And don't access settings.EMAIL_PROVIDERS directly.)
            if not api_key:
                # It's helpful to identify the alias in the error message.
                raise ImproperlyConfigured(
                    f"Add 'api_key' to EMAIL_PROVIDERS['{alias}']['OPTIONS']")
            self.api_key = api_key
            self.region = region or self.DEFAULT_REGION
        else:
            # 4. Being initialized from deprecated settings or in an older Django version.
            #    Use the original logic.
            self.api_key = api_key or getattr(settings, "WHEEMAIL_API_KEY", None)
            self.region = region or getattr(settings, "WHEEMAIL_REGION", self.DEFAULT_REGION)
            if not self.api_key:
                raise ImproperlyConfigured("Add WHEEMAIL_API_KEY to your settings")
```

After the deprecation period, sections 2 and 4 can be removed. (Or they can 
be omitted immediately if this is a first-party EmailBackend implemented in 
the same project that uses it.)


### Upgrading a wrapper EmailBackend

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
* Follow the [instructions above](#upgrading-emailbackend-implementations), which apply generally to all
  EmailBackend implementations
* When initializing from updated settings (`alias is not None`):
  * Accept a new `provider` parameter that identifies the provider alias
    to wrap
  * Where the wrapper backend previously called
    `mail.get_connection(settings.WRAPPED_EMAIL_BACKEND)`,
    instead use `mail.providers[provider]`

With that change, the updated settings from the django-mailer example above 
would be:

```python
EMAIL_PROVIDERS = {
    "default": {
        "BACKEND": "mailer.backend.DbBackend",
        "OPTIONS": {
            # Replaces MAILER_EMAIL_BACKEND setting:
            "provider": "wrapped",
        },
    },
    "wrapped": {
        "BACKEND": "anymail.backends.amazon_ses.EmailBackend",
    },
}
```

The indirection through `provider` also allows specifying different instances
of the wrapper backend for different needs:

```python
EMAIL_PROVIDERS |= {
    # ... extending above example
    "notifications-eu": {
        "BACKEND": "mailer.backend.DbBackend",
        "OPTIONS": {
            "provider": "wrapped-eu",
        },
    },
    "wrapped-eu": {
        "BACKEND": "anymail.backends.mailtrap.EmailBackend",
    },
}
```

If a wrapper is not designed to support multiple instances, it could 
prevent that by requiring that `alias == "default"` in its own backend 
constructor. Or instead of implementing a variable `provider` option as 
described above, it could instead use a fixed alias: e.g., `mail.providers
["mailer-wrapped"]`.

[django-celery-email]: https://pypi.org/project/django-celery-email/
[django-mailer]: https://pypi.org/project/django-mailer/


## django-upgrade recommendations

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

Things get tricker if a project uses multiple email backends, e.g., via 
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

# Some tests use filebased.EmailBackend.
if sys.argv[1:2] == ["test"]:
    EMAIL_FILE_PATH = "tests/mail/__snapshot__"
```

Apart from settings, django-upgrade could also:
* convert calls to `mail.get_connection()` with no args
  to `mail.providers.default`
* remove unnecessary `fail_silently=False` args from calls
  to django.core.mail APIs
* remove unnecessary `connection=mail.get_connection()` args (where
  `get_connection()` is called with no args) from calls to django.core.mail
  APIs (but not `connection=foo` where `foo = mail.get_connection()` and is
  being used to share a single connection between calls)

[django-upgrade]: https://django-upgrade.readthedocs.io/


## Future work

This section describes some **potential, future,** related features that 
are *not* part of this proposal but may help inform some of the design 
decisions here.

### Future: Password reset email provider

(See related discussion in [*Upgrading packages that send
email*](#upgrading-packages-that-send-email) above.)

Currently, using a different email provider for a django.contrib.auth 
password reset email requires subclassing `PasswordResetForm` to override 
`send_mail()`. Swapping in a different `provider` (or `connection` in 
earlier Django versions) isn't possible without also duplicating [all the 
email rendering logic][PasswordResetForm.send_mail].

[PasswordResetForm.send_mail]: https://github.com/django/django/blob/7bc9d39fbdae6c09f630c6e5d51ea4ad2484fc46/django/contrib/auth/forms.py#L394-L421

This could be improved by refactoring `PasswordResetForm` with better 
extension points (or a new setting), but another solution would be to check 
for a named `"password-reset"` email provider and fall back to the default 
provider:

```python
# django/contrib/auth/forms.py
class PasswordResetForm:
    ...
    def send_mail(self, ...):
        ...
        connection = mail.providers.get("password-reset") or mail.providers.default
        email_message = EmailMultiAlternatives(..., connection=connection)
        ...
        email_message.send()
```

(Because `connection=None` is handled as the default provider, it would be 
sufficient to write `EmailMultiAlternatives(...,
connection=mail.providers.get("password-reset"))`.)

Then users could optionally supply a "password-reset" alias in
`EMAIL_PROVIDERS`:

```python
# settings.py
EMAIL_PROVIDERS = {
    "default": {...}, 
    "notifications": {...},
}
# Also use the "notifications" provider for password reset messages:
EMAIL_PROVIDERS["password-reset"] = EMAIL_PROVIDERS["notifications"]
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

In anticipation of a feature like this, the current `EMAIL_PROVIDERS` proposal:
* Uses a nested `"OPTIONS"` dict rather than listing EmailBackend parameters
  at the same level as `"BACKEND"`.
* Uses a string `provider="alias"` argument rather than an EmailBackend
  instance

[ticket-35365#comment:7]: https://code.djangoproject.com/ticket/35365#comment:7
[anymail-send-defaults]: https://anymail.dev/en/stable/sending/anymail_additions/#global-send-defaults


### Future: Cached `providers`

Although EmailBackend instances are [not cacheable in
general](#providers-instances-are-not-cached), specific EmailBackend 
implementations may be. For example, Django's SMTP EmailBackend is cacheable
and reusable within a single thread (though cannot be shared between threads
as currently implemented).

We could allow backends to opt into `mail.providers` caching via a future
`cacheable` class property:

```python
# django.core.mail.backends.smtp

class EmailBackend(BaseEmailBackend):
    cacheable = True
    ...
```

With this change, `mail.providers` would be implemented using 
django.utils.BaseConnectionHandler (overriding `__getitem__()` to ensure 
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


## Motivation

(See the original [django-developers discussion] for more details and 
use cases.)

It's common to use different email services—or different configurations of 
the same email service—for different types of email:
* transactional notifications vs. bulk marketing
* internal operational reporting vs. email to end users
* different providers for specific geographic regions
* etc.

Django's pluggable email backends and `mail.get_connection()` API do not 
adequately support this. And as a consequence, packages that send email 
offer inconsistent (and sometimes complicated) extension points for 
overriding the email service to use.

Also, the general reluctance to add new top-level settings has been a 
blocking factor for some proposed features and fixes in Django's email 
handling. Moving EmailBackend-specific settings from the top level into 
`EMAIL_PROVIDERS` OPTIONS dicts allows that work to progress.

Prior art: The django-lorien-common package implemented a similar 
dictionary-based `EMAIL_CONNECTIONS` setting with a `get_custom_connection()` 
function to create EmailBackend instances from it: 
[django-lorien-common/common/mail.py].

[django-lorien-common/common/mail.py]: https://github.com/govtrack/django-lorien-common/blob/27241ff72536b442dfd64fad8589398b8a6e9f4d/common/mail.py


## Reference implementation

Django [PR #18421] by Jacob Rief provides a mostly complete implementation
of dictionary-based email providers, based on an earlier understanding of 
the goals. Some differences from this proposal:
* The PR doesn't have `mail.providers` (it retains `mail.get_connection()`
  as the way to create EmailBackend instances)
* `mail.get_connection()` accepts a new `provider` arg (which is mutually
  exclusive with the existing `backend` dotted import path arg)
* The `alias` EmailBackend constructor arg described here is instead named
  `provider` in the PR
* Because `get_connection()` is not deprecated:
  * It doesn't need to deprecate `auth_user` or `auth_password`
  * It avoids the `fail_silently` problem (`get_connection()` is basically 
    option 6 from the earlier discussion)


## AI disclosure

AI assistance was used for:
* Investigating implications of caching EmailBackend instances (GPT-5.2)
* Proofreading and technical review (Claude 4.6 Opus, which first suggested
  what became `fail_silently` option 3; Gemini 3 Pro)
* Updating the table of contents (JetBrains AI in-editor code generation)


## Copyright

This document has been placed in the public domain per the Creative
Commons CC0 1.0 Universal license
(<http://creativecommons.org/publicdomain/zero/1.0/deed>).

(All DEPs must include this exact copyright statement.)
