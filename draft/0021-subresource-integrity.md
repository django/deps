---
DEP: 0021
Author: Johannes Maron
Implementation Team: TBD
Shepherd: TBD
Status: Draft
Type: Feature
Created: 2026-09-23
---
# DEP 0021: Subresource Integrity support

Table of Contents
- [Abstract](#abstract)
- [Specification](#specification)
- [Motivation](#motivation)
- [Rationale](#rationale)
- [Backwards Compatibility](#backwards-compatibility)
- [Open Questions](#open-questions)
- [Reference Implementation](#reference-implementation)
- [Copyright](#copyright)

## Abstract

Subresource Integrity pins the digest of every script and stylesheet a page
loads.[^sri] The browser hashes each file again before it runs it. A mismatch
stops the file.

Where CSP[^csp] limits **who** is allowed to execute scripts, SRI limits **what**
those files contain. Django needs both to withstand supply-chain attacks.[^owasp]

This DEP has two phases that ship independently. Phase 1 gives Django a way to
produce integrity digest for static files. Phase 2 adds policy enforcement via
the `Integrity-Policy` and `Integrity-Policy-Report-Only` headers, analogue to CSP.

## Specification

### Phase 1: Providing integrity digests

The return value is the integrity metadata: one or more items of the form
`<algorithm>-<base64 digest>`, separated by spaces. That string is the value
of the `integrity` attribute. An algorithm may repeat with a different digest
when several versions of the file are acceptable.
See also: https://www.w3.org/TR/sri/#agility

Django's own storage backends return every algorithm, which currently is
`sha256`, `sha384` and `sha512`. A third-party storage may return fewer.

#### `Storage.integrity()`

```python
import base64
import enum
import dataclasses


class IntegrityAlgorith(enum.StrEnum):
    SHA256 = "sha256"
    SHA384 = "sha384"
    SHA512 = "sha512"
    

@dataclasses.dataclass(slots=True, frozen=True)
class IntegrityMetadata:
    algorithm: IntegrityAlgorith
    digest: bytes = dataclasses.field(doc="Hash digest.")
    
    def __str__(self):
        return f"{self.algorithm}-{base64.b64encode(self.digest).decode()}"

    
class IntegrityMetadataList(list[IntegrityMetadata]):
    
    def __str__(self):
        return " ".join(str(metadata) for metadata in self)
    
    def __html__(self):
        return str(self)


class Storage:
    def integrity(self, path) -> IntegrityMetadataList:
        """Return 1..N space-separated <algorithm>-<base64-digest> pairs."""
        raise NotImplementedError("Storage backend does not support Subresource Integrity (SRI).")
```

- `path` resolves like `Storage.url()`, so both `app/js/site.js` and a hashed name
  are valid.
- Raises
  - `NotImplementedError` if the file can't be digested,
  - `ValueError` (or specific subclass) if the path does not exist,
  - `ValueError`  (or specific subclass) if the path is not a file.
- A storage can precompute the digests while files are collected, or cache them
  after a first call, and neither the signature nor the caller changes.

#### `FieldFile.integrity()`

```python
class FieldFile:
    def integrity(self) -> IntegrityMetadataList:
        return self._storage.integrity(self.name)
```

> [!NOTE]
> Caching is integral to prevent I/O during template rendering.
> Therefore, the actual digest integration sits with the
> storage, enabling this storage to maintain a path-digest map.

#### Render path

##### Templates

A small Django sprint vote was in favor or extending the current `static` tag,
instead of a separate tag to acquire the integrity digests. Resulting in a
usage like so:

```html+django
{% load static %}

{% static "path/to/file.js" as asset %}
<script src="{{ asset.url }}" integrity="{{ asset.integrity }}"></script>
{# for backwards compatibility, __str__ defaults to .url #}
<script src="{{ asset }}" integrity="{{ asset.integrity }}"></script>
{# 'static' without name assigning remains to function as before #}
<script src="{% static 'path/to/file.js' %}"></script>
```

The `static`-templatetage currently adds a URI-string to the context. That
string should be replaced with some kind of discrete, backwards compatible,
string-like object, like so:

```diff
diff --git a/django/templatetags/static.py b/django/templatetags/static.py
index a68e44add2..3d97a71b65 100644
--- a/django/templatetags/static.py
+++ b/django/templatetags/static.py
@@ -1,9 +1,11 @@
 from urllib.parse import quote, urljoin
 
 from django import template
 from django.apps import apps
 from django.utils.encoding import iri_to_uri
 from django.utils.html import conditional_escape
 
 register = template.Library()
 
@@ -92,6 +94,19 @@ def get_media_prefix(parser, token):
     return PrefixNode.handle_token(parser, token, "MEDIA_URL")
 
 
+class StaticFile(str):
+    __slots__ = ("url", "integrity")
+
+    @property
+    def url(self): ...
+
+    @property
+    def integrity(self): ...
+
+
 class StaticNode(template.Node):
     child_nodelists = ()
 
@@ -118,7 +133,7 @@ class StaticNode(template.Node):
             url = conditional_escape(url)
         if self.varname is None:
             return url
-        context[self.varname] = url
+        context[self.varname] = StaticFile(path=self.path.resolve(context))
         return ""
 
     @classmethod
```
##### Forms

`MediaAsset.render()` adds the attribute, so `Script` and `Stylesheet` both get
it. Django 6.1 already wraps plain string paths in those classes, and a project
needs no change to its form definitions.

Therefore, only relatively small changes need to include the integrity attribute.

```python
class MediaAsset:
    # ... existing parent class to Script & Stylesheet
    
    def render(self, *, attrs=None):
        # integrity calls should only happen during render-time and not
        # during init-time / module loading to prevent slow app startups
        attrs = attrs or {}
        try:
            attrs["integrity"] = self.integrity
        except NotImplementedError:
            pass
        attributes = flatatt({**(attrs or {}), **self.attributes})
        ...
    
    @property
    def integrity(self) -> IntegrityMetadataList:
        if apps.is_installed("django.contrib.staticfiles"):
            from django.contrib.staticfiles.storage import staticfiles_storage
            return staticfiles_storage.integrity(self._path)
        raise NotImplementedError
```

With those small adjustments, forms will automatically render with SRI digests as follows:

```python
from django import forms


class ContactForm(forms.Form):
    class Media:
        js = ["app/js/form.js"]
        css = {"all": ["app/css/form.css"]}
```

```html
<link href="/static/app/css/form.css" rel="stylesheet" media="all"
      integrity="sha256-<BASE64> sha384-<BASE64> sha512-<BASE64>">
<script src="/static/app/js/form.js"
        integrity="sha256-<BASE64> sha384-<BASE64> sha512-<BASE64>"></script>
```


### Phase 2: `Integrity-Policy` headers

This phase copies CSP, names included, so a reader who knows one knows the
other.[^csp]


`django.utils.sri` holds the shared vocabulary, in the style of
`django.utils.csp`.

```python
from enum import StrEnum

class SRIHeader(StrEnum):
    INTEGRITY_POLICY = "Integrity-Policy"
    INTEGRITY_POLICY_REPORT_ONLY = "Integrity-Policy-Report-Only"


class SRIDestination(StrEnum):
    SCRIPT = "script"
    STYLE = "style"

    
class SRISource(StrEnum):
    INLINE = "inline"


def build_policy(policy) -> str:
    """Render a policy into a header value."""
```

> [!NOTE]
> During the sprint @jacobtylerwalls and @codingjoe discussed that the single StrEnum
> in CSP is a bit awkward and decided we don't want to repeat the "wrong version" twice.

#### Middleware

```python
from django.conf import settings
from django.middleware import MiddlewareMixin
from django.utils.sri import SRIHeader, build_policy


class IntegrityPolicyMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        sentinel = object()
        config = getattr(response, "_integrity_policy_config", sentinel)
        if config is sentinel:
            config = settings.SECURE_INTEGRITY_POLICY
        ro_config = getattr(response, "_integrity_policy_ro_config", sentinel)
        if ro_config is sentinel:
            ro_config = settings.SECURE_INTEGRITY_POLICY_REPORT_ONLY

        for header, policy in [
            (SRIHeader.INTEGRITY_POLICY, config),
            (SRIHeader.INTEGRITY_POLICY_REPORT_ONLY, ro_config),
        ]:
            # Do not change a header a view already set. An empty policy
            # gives no header.
            if policy and header not in response:
                response.headers[str(header)] = build_policy(policy)

        return response
```

There is no `process_request` hook, because CSP has one only for the nonce.
Settings are read for each response rather than cached, so `override_settings()`
works without signal wiring. A header already on the response is never overwritten.

#### Settings

`SECURE_INTEGRITY_POLICY`, default `{}`.

- `blocked-destinations` (required): one or more of `SRIDestination.SCRIPT` and
  `SRIDestination.STYLE`. A request for those destinations must carry integrity metadata,
  and a `no-cors` request is blocked outright.
- `sources` (optional): `SRISource.INLINE` is the only value the standard defines, and
  it is the default.
- `endpoints` (optional): names defined in a `Reporting-Endpoints` header, which
  Django does not supply. The same position CSP takes on reports.

`SECURE_INTEGRITY_POLICY_REPORT_ONLY`, default `{}`, renders the
`Integrity-Policy-Report-Only` header. Nothing is blocked. This is how a live
site adopts enforcement without breaking pages.

```python
from django.utils.sri import SRIDestination, SRISource 

SECURE_INTEGRITY_POLICY = {
    "blocked-destinations": [SRIDestination.SCRIPT, SRIDestination.STYLE],
    "sources": [SRISource.INLINE],
}
```

```http
Integrity-Policy: blocked-destinations=(script style), sources=(inline)
```

#### Decorators

`django/views/decorators/integrity.py` follows the CSP decorator shape, including
the `TypeError` on a non-mapping policy and the branch for async views.

- `integrity_policy_override(config)` sets `response._integrity_policy_config`.
  An empty mapping removes the header from that view.
- `integrity_policy_report_only_override(config)` does the same through
  `response._integrity_policy_ro_config`.

```python
from django.http import HttpResponse
from django.utils.sri import SRIDestination
from django.views.decorators.integrity import integrity_policy_override


@integrity_policy_override({"blocked-destinations": [SRIDestination.SCRIPT]})
def my_view(request):
    return HttpResponse("Scripts without integrity metadata are blocked")
```

#### System checks

Both are registered with `@register(Tags.security)` and not `deploy=True`, so
they also fire in development.[^checkids]

- `check_integrity_policy_settings()` reports an `Error` when a setting is not a
  mapping, or when `build_policy()` rejects it. `manage.py check` catches a bad
  policy instead of a request.
- `check_integrity_policy_debug()` warns when a policy is enforced with `DEBUG`
  on. Phase 1 emits nothing in development, so the browser blocks every script
  and stylesheet.

### Adoption

1. Serve static files from a storage that can produce integrity digests, or run
   `collectstatic` if the storage precomputes them.
2. Add `IntegrityPolicyMiddleware` to `MIDDLEWARE`.
3. Set `SECURE_INTEGRITY_POLICY_REPORT_ONLY`.
4. Read the reports.
5. Move the mapping to `SECURE_INTEGRITY_POLICY`.

The position in `MIDDLEWARE` does not matter, because the middleware only adds
headers that are absent.

Step 5 has a precondition. Every script and stylesheet on a page needs
integrity digests, or the browser blocks it.

## Motivation

Supply chain failures rank third in the OWASP Top 10.[^owasp] The browser is the
only place where they get caught. A CDN, a vendor, or a storage backend can hold a
valid certificate and still serve modified JavaScript. Nothing on the server
notices, because the page asked for exactly that URL.

Django is unusually well-placed to produce this metadata. It holds the bytes it
collects, including the CSS and JavaScript it rewrites during post-processing. A
third-party package has a file on disk and a hope that the storage serves the
same one. It chooses the names it serves, and a hashed name keeps a digest
true. It renders form media assets itself, so the attributes arrive without a tag
in every template.

Neither existing package covers that ground. `django-sri` hashes from the
filesystem, which rules out a storage without `path()` and needs a tag per
template. `django-integrity-policy` handles the header and nothing else.

## Rationale

Hashing belongs to the file, and asking belongs to the storage. A storage 
decides where the answer comes from a cache (no-I/O) or a filesystem.

Three digests by default. The standard negotiates: the server publishes a set,
and the client picks the strongest algorithm it supports.[^agility] Three digests
cost one read and three hash operations, and no extra request. A single algorithm
ages badly. A browser that stops trusting SHA-256 cannot negotiate upward, while
a client on slow hardware stays free to take the short digest. Third-party
storages can return any number.

Attributes on by default. A feature behind an opt-in setting stays unused, and the
safety property already lives in the storage.

The header copies CSP. Django 6.0 set the pattern, and reading the settings for
each response keeps `override_settings()` working. I chose
`SECURE_INTEGRITY_POLICY` over the `SECURE_SRI` as the acronym may not be
well-known as the more commen `integrity`-attribute touchpoint for users.

### Rejected Designs

- Rewriting HTML in middleware. [django-debug-toolbar][debug-toolbar-middleware],
  [django-browser-reload][browser-reload-middleware], and
  [django-minify-html][django-minify-html] all do it, and share the same three
  guards: not streaming, not encoded, `text/html`. `django-minify-html` must also
  be listed above the other two, so each rewriter adds a `MIDDLEWARE` ordering
  contract, and every skipped response silently loses the attribute. Phase 1
  avoids both, because the template knows the digest.
- CSP hash source expressions. Similar syntax, different question. SRI decides
  which file an element loads, CSP decides what the page can run.

## Backwards Compatibility

Form media assets gain `integrity` attributes when the storage implements
`integrity()`, so a project sees this after an upgrade, whether or not it wanted
SRI.

> [!WARNING]:
> A project that rewrites static bytes in transit must make its storage
> return an empty string. However, the whole point is to prevent in transit
> changes to files.

`Storage.integrity()` is a new method on a public base class, so a third-party
storage that already has an `integrity` attribute loses it silently.
However, no such precedent is known to the authors. 

Phase 2 is additive and enforces nothing until a project configures it.

## Open Questions

These are the open API decisions. The rest belongs to the implementation.

1. **A path the storage cannot answer for.** An absolute third-party URL, or a
   name it will not hash. An empty string, or `NotImplementedError`? The same
   choice decides how a project opts out of attributes.
2. **`crossorigin` for a file on another origin.** Integrity verification needs a
   CORS-enabled request, and browsers refuse a `no-cors` request that carries
   integrity metadata.[^cors] So `integrity` without `crossorigin` blocks the
   file. Does the render path add `crossorigin` when `STATIC_URL` has a host, or
   does the project pass it per asset?

## Reference Implementation

Worth reading: [django-sri][django-sri] for the digest calculation, the template
tags and the `DEBUG` suppression,
[django-integrity-policy][django-integrity-policy] for the middleware, the header
construction and the decorators, and Django 6.0's CSP support for the shape of
phase 2.

The work:

- `django/utils/sri.py`: `SRIHeader`, `SRIDestination`, `SRISource`, and
  `build_policy()`.
- `Storage.integrity()`.
- `FieldFile.integrity()` in `django/db/models/fields/files.py`.
- `StaticNode.integrity()` in `django/templatetags/static.py`.
- Integrity injection in `MediaAsset.render()`.
- `django/middleware/integrity.py`, `django/views/decorators/integrity.py`, two
  settings and two checks.
- Docs: `docs/ref/integrity.txt` and `docs/howto/integrity.txt` beside the CSP
  pages, plus `docs/ref/files/storage.txt`, `docs/ref/settings.txt`,
  `docs/topics/security.txt`, `docs/topics/forms/media.txt` and the release
  notes.
- Tests: `tests/utils_tests/test_sri.py`, `tests/file_storage/`, `tests/files/`,
  `tests/forms_tests/`, `tests/template_tests/`,
  `tests/middleware/test_integrity.py`, `tests/decorators/test_integrity.py` and
  `tests/check_framework/test_security.py`. One test covers `integrity` and the
  CSP nonce attribute on a single element.

## Copyright

This document has been placed in the public domain per the Creative Commons CC0
1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).

[^sri]: The standard and a shorter overview: [W3C specification][sri-spec] and
    [MDN][sri-mdn].

[^csp]: Django's CSP guide and reference: [how-to][csp-howto] and
    [reference][csp-ref].

[^cors]: Subresource Integrity needs a CORS-enabled request, and a browser
    refuses a `no-cors` request that carries integrity metadata. For `script` and
    `link` that means `crossorigin="anonymous"`, and a server that sends
    `Access-Control-Allow-Origin`. The [MDN overview][sri-mdn] covers both.

[^checkids]: `security.E026` and `security.W027` are the CSP equivalents in
    Django 6.1. The new identifiers are the next free ones, `security.E028` and
    `security.W029`.

[^agility]: The standard calls this [agility][sri-agility].

[^owasp]: [A03 Software Supply Chain Failures][owasp-a03].

[debug-toolbar-middleware]: https://github.com/django-commons/django-debug-toolbar/blob/main/debug_toolbar/middleware.py
[browser-reload-middleware]: https://github.com/adamchainz/django-browser-reload/blob/main/src/django_browser_reload/middleware.py
[django-minify-html]: https://github.com/adamchainz/django-minify-html
[django-sri]: https://github.com/RealOrangeOne/django-sri
[django-integrity-policy]: https://github.com/adamchainz/django-integrity-policy
[sri-spec]: https://www.w3.org/TR/sri/
[sri-mdn]: https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Subresource_Integrity
[sri-agility]: https://www.w3.org/TR/sri/#agility
[csp-howto]: https://docs.djangoproject.com/en/stable/howto/csp/
[csp-ref]: https://docs.djangoproject.com/en/stable/ref/csp/
[owasp-a03]: https://owasp.org/Top10/2025/A03_2025-Software_Supply_Chain_Failures/
