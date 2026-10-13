======================================
DEP 0022: Adding import maps to Django
======================================

:DEP: 0022
:Author: Matthias Kestenholz
:Implementation Team: Matthias Kestenholz
:Shepherd: You?
:Status: Draft
:Type: Feature
:Created: 2023-12-12

.. contents:: Table of Contents
   :depth: 3
   :local:

The first draft of this DEP was written by Thibaud Colas years ago. It has
also been discussed in the `Django forum
<https://forum.djangoproject.com/t/rejuvenating-vs-deprecating-form-media/21285>`__.
The current version has deviated a lot but still owes its existence to this.
Parts of the original draft have landed in Django 6.1 already (``Stylesheet``,
CSP nonces for media); import maps are one of the remaining pieces.

Abstract
========

ES modules import each other by URL. When static file storages add hashes to
file names for cache busting, those URLs change on every deployment. Import
maps solve this using a web standard: Modules import stable identifiers such as
``my-library``, and the import map tells the browser which file to actually
load.

Browser support for multiple import maps is spotty at the time of writing.
Chromium and Safari support multiple import maps since early 2025, but Firefox
still only uses the first import map and ignores all others unless users enable the
implementation explicitly in their browsers (see `MDN
<https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/script/type/importmap>`__).
This means that when we want to use import maps, we have to ensure that there's
only a single import map in the output or wait for years until we can use this
feature.

Django has the ``Media`` mechanism from ``django.forms`` for specifying CSS and
JavaScript assets used in forms, widgets or parts of the administration
interface. By using ``Media`` objects, some parts of Django know how to
collect, order and output required assets.

This DEP proposes adding support for import maps to Django and allowing to use
import maps with ``Media``: A new ``ImportMap`` class, a single import map per
``Media`` object which is merged when media objects are added together and
rendered before all scripts, and moving the asset classes to a new
``django.utils.assets`` module.


Specification
=============

The implementation requires several parts which are described in the following
sections.


Import map objects
------------------

The new ``ImportMap`` class allows creating import map instances which hold the
map itself and additional information like integrity hashes. The import map
format is defined by the `HTML standard
<https://html.spec.whatwg.org/multipage/webappapis.html#import-maps>`__, `MDN
<https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/script/type/importmap>`__
has a good introduction.

The API follows. It is also implemented for current Django versions by
`django-js-asset <https://github.com/feincms/django-js-asset>`_ (see
`Reference Implementation`_).

.. code-block:: python

    class ImportMap:
        """
        An import map, rendered as ``<script type="importmap">``.

        ``imports``, ``scopes`` and ``integrity`` are the parts of the import
        map with the same names.

        Paths in ``imports`` and ``scopes`` are resolved when rendering, like
        ``Script`` paths: Relative paths are passed through ``static()``, while
        URLs with a scheme and paths starting with ``/`` are used as they are.
        Scope prefixes are never resolved.

        For paths resolved through ``static()``, ``integrity`` metadata is added
        automatically if the static files storage supports it (see `Deferred
        functionality`_). Specifying ``integrity`` explicitly is therefore only
        needed for files hosted elsewhere, e.g. modules loaded from a CDN.

        The data is copied. ``attributes`` are added to the ``<script>``
        element, like for ``Script`` and ``Stylesheet``.
        """

        def __init__(
            self,
            imports: dict[str, str] | None = None,
            *,
            scopes: dict[str, dict[str, str]] | None = None,
            integrity: dict[str, str] | None = None,
            **attributes: str | bool,
        ) -> None: ...

        def render(self, *, attrs: dict[str, str | bool] | None = None) -> str:
            """
            Render the ``<script type="importmap">`` element. The import map
            with resolved paths is serialized as JSON and escaped using
            ``json_script()``. ``attrs`` are added like in
            ``MediaAsset.render()`` (raising a ``ValueError`` for conflicting
            attributes), e.g. for CSP nonces.
            """

        def __eq__(self, other: object) -> bool: ...

        def __or__(self, other: ImportMap) -> ImportMap:
            """
            Each scope in ``scopes`` is merged separately.
            """

This allows us to build and render import map objects:

.. code-block:: python

    def view(request, ...):
        importmap = ImportMap({
            "my-library": "my-app/my-library.js",
        })
        return render(request, "template.html", {
            "importmap": importmap,
        })

Import map objects can be merged together using ``map1 | map2`` (similar to
dictionary merging). The same key in a latter import map replaces values in the
former; this also applies to attributes. This is intentional since, for
example, overriding entries a third party app provided should be possible.

Import map objects copy the data they are given and should be treated as
immutable; merging always returns a new import map, and ``map1 |= map2`` binds
a new object to ``map1``.

Calling ``static()`` inside a ``class Media`` definition resolves the path at
import time, which doesn't work well with static file storages which modify
file names, for example ``ManifestStaticFilesStorage``. Import maps therefore
resolve paths when rendering, like ``Script`` does. This makes it possible to
define import maps at module level.


Teaching ``Media`` about import maps
------------------------------------

Suppose a ``ModelAdmin`` class wants to use ES modules and import maps. We can
achieve that as follows:

.. code-block:: python

    @admin.register(models.Question)
    class QuestionModelAdmin(admin.ModelAdmin):
        class Media:
            importmap = ImportMap({"my-library": "my-app/my-library.js"})
            js = [Script("my-app/my-module.js", type="module")]

Each media object holds a single import map in addition to its CSS and
JavaScript. If a media definition needs entries from several import maps, they
have to be merged using ``|`` first. When media objects are added together,
their import maps are merged as well, so a page still ends up with a single
import map. The import map is rendered first, since otherwise the map only
affects the modules coming after it in the HTML source.

.. code-block:: python

    class Media:
        def __init__(
            self, media=None, css=None, js=None, importmap: ImportMap | None = None
        ) -> None:
            """
            ``importmap`` is a single ``ImportMap``. Media definitions
            (``class Media``) can define an ``importmap`` attribute as well.
            """

        def __add__(self, other: Media) -> Media:
            """
            Combine the CSS and JavaScript as before, and merge the import maps
            using ``|``. Entries of the media added later win.
            """

        def __getitem__(self, name: str) -> Media:
            """
            ``media["importmap"]`` (``{{ media.importmap }}`` in templates)
            returns a media object containing only the import map, like
            ``media["css"]`` and ``media["js"]`` do for CSS and JavaScript.
            """

        def render(self, *, attrs: dict[str, str | bool] | None = None) -> str:
            """
            Render the import map, the CSS and the JavaScript, in this order.
            """

        def render_importmap(
            self, *, attrs: dict[str, str | bool] | None = None
        ) -> list[str]:
            """
            Return a list containing the rendered import map, or an empty list.
            """

The import map is stored in an ``_importmap`` attribute next to ``_css_lists``
and ``_js_lists``, and ``"importmap"`` is added to ``MEDIA_TYPES`` before
``"css"`` and ``"js"``. Django's ``__getitem__``, which uses
``getattr(self, "_" + name)``, and ``render()``, which calls
``render_<name>()`` for each type, then work without further changes.
Templates which render ``{{ media.css }}`` and ``{{ media.js }}`` separately
have to render ``{{ media.importmap }}`` as well. The admin's
``change_list.html`` is updated accordingly.

Import maps are passed using the ``importmap`` argument or attribute only. When
rendering an import map found in a ``js`` list, ``Media`` raises a
``TypeError`` pointing to the ``importmap`` argument, since rendering it in
place would produce several import maps. [#js-lists]_

.. [#js-lists] The error also helps finding code written for django-js-asset
   4.x, which shipped import maps in ``js`` lists.


A complete example
------------------

The following example shows how the parts work together. The project defines a
base import map at module level, which works since paths are only resolved when
rendering:

.. code-block:: python

    # myproject/assets.py
    from django.utils.assets import ImportMap, Media, Script

    project_media = Media(
        importmap=ImportMap({"lit": "vendor/lit.js"}),
        js=[Script("myproject/base.js", type="module")],
    )

Two third party apps ship widgets which use ES modules. Both of them depend on
`Lit <https://lit.dev/>`__ and ship their own copy of it. (All copies of Lit in
this example are single-file bundles, since the npm package imports further
packages which would need their own import map entries.)

.. code-block:: python

    # markdown_editor/widgets.py
    class MarkdownEditorWidget(forms.Textarea):
        class Media:
            importmap = ImportMap({
                "lit": "markdown_editor/lit.js",
                "markdown-editor": "markdown_editor/editor.js",
            })
            js = [Script("markdown_editor/init.js", type="module")]

    # date_picker/widgets.py
    class DatePickerWidget(forms.DateInput):
        class Media:
            importmap = ImportMap({
                "lit": "date_picker/lit.js",
                "date-picker": "date_picker/date-picker.js",
            })
            js = [Script("date_picker/init.js", type="module")]

A view uses two forms with those widgets. The media of the forms and of the
project are added together; the project's media is added last so that its
import map entries win:

.. code-block:: python

    class ArticleForm(forms.ModelForm):
        class Meta:
            model = Article
            fields = ["title", "body", "publication_date"]
            widgets = {
                "body": MarkdownEditorWidget,
                "publication_date": DatePickerWidget,
            }

    class CommentForm(forms.Form):
        text = forms.CharField(widget=MarkdownEditorWidget)

    def edit_article(request, pk):
        article = get_object_or_404(Article, pk=pk)
        form = ArticleForm(instance=article)
        comment_form = CommentForm()
        return render(request, "articles/edit.html", {
            "form": form,
            "comment_form": comment_form,
            "media": form.media + comment_form.media + project_media,
        })

The template renders the import map, the CSS and the JavaScript separately in
the ``<head>`` (``{% csp_nonce_attr media %}`` renders the same), and the forms
without their media:

.. code-block:: html+django

    <head>
      {# The nonce requires CSP to be configured. #}
      {% csp_nonce_attr media.importmap %}
      {% csp_nonce_attr media.css %}
      {% csp_nonce_attr media.js %}
    </head>
    <body>
      <form method="post">{% csrf_token %}{{ form }}</form>
      <form method="post">{% csrf_token %}{{ comment_form }}</form>
    </body>

This renders a single import map before all scripts. The paths contain hashes
when using ``ManifestStaticFilesStorage`` (shortened here):

.. code-block:: html

    <script type="importmap" nonce="...">{"imports": {
      "lit": "/static/vendor/lit.1a2b.js",
      "markdown-editor": "/static/markdown_editor/editor.3c4d.js",
      "date-picker": "/static/date_picker/date-picker.5e6f.js"
    }}</script>
    <script src="/static/markdown_editor/init.7a8b.js" nonce="..." type="module"></script>
    <script src="/static/date_picker/init.9c0d.js" nonce="..." type="module"></script>
    <script src="/static/myproject/base.1e2f.js" nonce="..." type="module"></script>

The ``MarkdownEditorWidget`` is used in both forms, but its assets are only
included once. Only one copy of Lit is loaded, and the project decides which
one. The apps' own ``lit`` entries are still useful: Without the project's
entry, the markdown editor's copy would be used for both widgets, since the
comment form adds its media again after the date picker's (see `Merging
order`_).

Either way, both widgets end up using the same copy of Lit. This only works if
both widgets are compatible with that version of Lit. If they aren't, one of
the widgets breaks in the browser, and nothing warns about it. An app which
really needs a specific copy of a library has to namespace the entry or use
``scopes`` instead (see `Rationale`_).

The JavaScript modules use the stable identifiers from the import map and don't
have to know about hashed file names. Modules of the same app should import
each other through the import map as well. A relative import such as
``import "./editor.js"`` in ``init.js`` is resolved to
``/static/markdown_editor/editor.js`` first, and since the import map has no
entry for that URL, the browser would load the file without the hash, and
possibly a second copy of the module:

.. code-block:: javascript

    // markdown_editor/static/markdown_editor/editor.js
    import { LitElement } from "lit"

    export class MarkdownEditor extends LitElement {
      // ...
    }

    // markdown_editor/static/markdown_editor/init.js
    import { MarkdownEditor } from "markdown-editor"

    customElements.define("markdown-editor", MarkdownEditor)

Templates can also render the media of each form next to the form, for example
when the HTML of forms and their scripts are loaded dynamically after the
initial page load. The import maps still have to be merged and rendered first.
Adding the media objects returned by ``media["importmap"]`` merges their import
maps:

.. code-block:: python

    def edit_article(request, pk):
        ...
        return render(request, "articles/edit.html", {
            "form": form,
            "comment_form": comment_form,
            "importmap": (
                form.media["importmap"]
                + comment_form.media["importmap"]
                + project_media["importmap"]
            ),
            "project_media": project_media,
        })

.. code-block:: html+django

    <head>
      {# The nonce requires CSP to be configured. #}
      {% csp_nonce_attr importmap %}

      {# We know that the project media only contains JavaScript #}
      {% csp_nonce_attr project_media.js %}
    </head>
    <body>
      <form method="post">
        {% csrf_token %}
        {% csp_nonce_attr form.media.css %}
        {% csp_nonce_attr form.media.js %}
        {{ form }}
      </form>
      <form method="post">
        {% csrf_token %}
        {% csp_nonce_attr comment_form.media.css %}
        {% csp_nonce_attr comment_form.media.js %}
        {{ comment_form }}
      </form>
    </body>

The CSS and JavaScript of ``form``'s and ``comment_form``'s media attributes
have to be rendered separately, otherwise the import maps would be rendered
again. This isn't a problem per se since the import map rendered in the head
already contains all of those entries and therefore the subsequent entries are
ignored (see `Merging order`_). It's just an aesthetic nuisance, and browsers
may report the ignored entries in the console.

Assets used by both forms are rendered once per form, though. Repeating module
scripts such as ``markdown_editor/init.js`` is harmless, since browsers only
evaluate a module once. Classic scripts would run twice, and stylesheets are
included twice.


Merging order
-------------

Import maps are merged in the order the media objects have been added
together, so a project's import map overrides entries of import maps added by
apps as long as the project's media is added last.

Adding the same media again merges its import map again, e.g. when a widget is
used in two forms. Its entries then win over entries of media added in between.
The CSS and JavaScript of such media is still only included once.

The admin adds ``ModelAdmin.media`` before the media of forms, widgets and
inlines, so an import map on a ``ModelAdmin`` cannot override entries of import
maps added by widgets.

Media rendered separately produces separate import maps, e.g. when rendering
``{{ form.media }}`` for each form. The recommended way is to add all media
objects together and render them once before any module scripts. If some of
that media is rendered again later on, it doesn't matter: Its import map only
contains specifiers which the first import map already maps. Browsers which only
support a single import map ignore the second one, and browsers which support
several import maps drop specifiers which are already mapped (see `MDN
<https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/script/type/importmap>`__).
The first import map's entries win either way, even when the values differ,
e.g. when the project overrides an app's entry. Browsers only behave
differently for specifiers which the first import map doesn't contain, which
happens when media is rendered without having been added to the media rendered
first.


Moving assets out of ``django.forms``
-------------------------------------

Import maps, scripts and stylesheets are useful outside of forms too, for
example when rendering the assets of a page in a view. The asset classes should
therefore move to a new ``django.utils.assets`` module containing
``ImportMap``, ``Media``, ``Script``, ``Stylesheet`` and ``static``.
``MediaAsset`` is the base class for object-based assets and is therefore also
moved.

The implementation of ``static()`` moves to ``django.utils.assets`` as well,
and ``django.templatetags.static`` uses it from there. ``static()`` checks
whether ``django.contrib.staticfiles`` is installed and uses its storage if it
is. This means that ``django.utils.assets`` uses the app registry, but that's
how ``static()`` already works now, and other modules in ``django.utils`` such
as ``django.utils.translation`` use the app registry too.

Deciding whether a path is passed through ``static()`` should also live in
``django.utils.assets``, as a small helper used by ``MediaAsset.path`` and
``ImportMap``. URLs with a scheme are detected the same way
``HashedFilesMixin.url_converter`` already does when post-processing CSS and
JavaScript files (``^[a-z]+:`` or starting with ``//``). This means that
``Script`` also leaves URLs with other schemes than ``http:`` and ``https:``
alone, such as ``data:`` URLs, which were passed through ``static()`` before.

The existing import paths (``django.forms.Media``,
``django.forms.widgets.Script``, ``django.templatetags.static.static`` etc.)
are deprecated and removed following Django's usual deprecation policy. Media
definitions using ``class Media`` on forms, widgets and model admins keep
working as before, they don't import anything.

A fixer for `django-upgrade <https://github.com/adamchainz/django-upgrade>`__
can automatically change the import paths in projects and would be a part of
the implementation plan, so the deprecation should hardly affect anyone.


Deferred functionality
----------------------

Calculating ``integrity`` metadata automatically depends on the static files
storage. The hashes have to be calculated from the files as they are served.
`DEP 0021 <https://github.com/django/deps/pull/122>`__ proposes
``Storage.integrity()`` for this and adds an ``integrity`` attribute when
rendering media assets. Modules loaded through an import map don't have a
``<script>`` element of their own, so ``ImportMap`` would add their hashes to
the ``integrity`` section of the import map instead when resolving paths.

The import map itself is an inline script, so CSP only allows it with a nonce,
``'unsafe-inline'`` or a hash of its contents in ``script-src``. A method
returning the hash of the rendered JSON would allow using a hash instead of a
nonce. It could return the ``IntegrityMetadataList`` proposed by DEP 0021,
which suggests naming it ``integrity()``, but that could be confused with the
``integrity`` section of the import map; ``csp_hash()`` would avoid that.
DEP 0021 leaves CSP hashes out of scope, and Django's CSP support doesn't
handle hash sources yet, so we're leaving it out for now as well.

A template tag for rendering the import map, similar to
``{% csp_nonce_attr media %}``, has also been considered. The tag could
remember that the import map has already been rendered and warn about entries
added afterwards. This only helps when all media is rendered through the tag,
so we're leaving it out for now.


Motivation
==========

Without import maps, the imports inside ES modules would have to be
rewritten on every deployment. ``ManifestStaticFilesStorage`` has an
experimental ``support_js_module_import_aggregation`` option which does this
using regular expressions. Import maps solve the same problem using a web
standard.

Third party apps can declare their own import maps, which allows them to
cleanly ship ES modules.

This only works for now if the whole page agrees on a single import map. When
several apps and the project itself want to use import maps, we need a common
mechanism to merge those maps so that we can produce a single import map at the
top of the page and not just let the first map win. If all browsers supported
multiple import maps, apps could ship their own maps. Until then, apps cannot
solve this on their own since they have to agree on a way of merging import
maps, and that's why the support should live in Django itself.

Even with full browser support, a single import map makes loading easier to
trace, since there's only one place to look up which file a specifier resolves
to.

``Media`` already collects assets from forms, widgets and the admin, so it is
the natural place to collect import maps too. Using ``Media`` isn't required
though; import maps can also be managed differently with the proposed
utilities.

The proposed design isn't tied to a particular way of generating import maps.
Import maps generated by other tools, such as `django-esm
<https://github.com/codingjoe/django-esm>`_ and `esimport
<https://github.com/codingjoe/esimport>`_, can be loaded into
``ImportMap`` objects and merged with everything else.


Rationale
=========

Several considerations led to the design proposed above.

Django has traditionally not picked a frontend technology. Import maps don't
conflict with this: unlike libraries or frameworks such as jQuery, htmx, React
or Svelte, they are the web platform's own mechanism for loading modules and
don't prescribe how the frontend is built.

A single global import map has been rejected. A variant of this would be
loading import maps from Django apps, e.g. an ``importmap.py`` module
automatically loaded at server start, as done by `dj-importmap
<https://github.com/betagouv/dj-importmap/blob/main/importmap/base.py>`__. A
global map contains all entries on every page, and it cannot be combined with
the assets forms and widgets already declare using ``Media``.

We don't want to tie the import map or forms generally to the request cycle.
Media is declared on classes and can be rendered without access to the request
today, and this should stay that way.

Rendering media first and injecting the import map at the top of the page in a
second pass has been rejected as well. `django-sekizai
<https://github.com/django-cms/django-sekizai>`__ would allow something like
this. Django's template rendering doesn't go back anywhere in core, and we can
avoid that complexity by being explicit about managing, merging and rendering
import maps.

Shipping import maps through the ``js=[]`` list has been considered as well.
Since import maps are most commonly used in JavaScript, this seems natural, and
``{{ media.js }}`` would include the import map automatically. However, the
import maps then take part in the topological sort done by ``Media.merge``,
which doesn't guarantee the order in which they are merged when import maps are
listed after other assets. Just rendering the import map alone would be
awkward because it would have to be pulled out of the list of JavaScript
assets. A separate ``importmap`` argument holding a single import map avoids
both problems.

Renaming ``Media`` to ``Assets`` when moving it out of ``django.forms``, as
proposed in `ticket #22298 <https://code.djangoproject.com/ticket/22298>`__,
has been rejected. Media definitions (``class Media``) and the ``media``
attribute of forms, widgets and model admins keep their names, so renaming
only the class would mix both names. Renaming everything would affect every
form and widget definition, which goes far beyond adding import maps.

Emitting a warning (similar to ``MediaOrderConflictWarning``) when the same key
is mapped to different values has been rejected. Overriding entries is a case
which we won't encounter often, but it is explicitly supported, and ``Media``
cannot distinguish an intentional override by the project from two apps
colliding by accident. The warning would therefore also fire for the supported
case. If an app really needs a specific copy of a module, for example of
``lit``, it can namespace the key (``my-app/lit``), use ``scopes`` which only
apply to modules loaded from a given path prefix, or not use the import map for
this module at all.

Relying on browser support for multiple import maps instead of merging them has
been rejected for now. Firefox has `implemented support
<https://bugzilla.mozilla.org/show_bug.cgi?id=1916277>`__ but hasn't `enabled
it <https://bugzilla.mozilla.org/show_bug.cgi?id=2021012>`__ at the time of
writing. Once it ships, it still takes about 30 months until the feature is
Baseline widely available, and some projects have to support older browsers
for even longer. Missing support isn't a visual glitch, it's a deal breaker.
Merged import maps keep working in browsers supporting multiple import
maps, so nothing has to change once they are widely available.

The design has been discussed at Django on the Med 2026 in Pescara, Italy.
There's no consensus yet, it's a first draft and doesn't solve all problems in
the space, but it should help get us moving.


Backwards Compatibility
=======================

If people are already using import maps in their own projects, they would have
to be aware of this change. For example, users of django-esm would have to be
prepared to load the import map back into Python to allow it to be merged with
import maps provided by other third party apps.

The asset classes moving to ``django.utils.assets`` doesn't break anything
since the old import paths stay available during the deprecation period, and
the django-upgrade fixer changes them automatically.

Templates which render ``{{ media.css }}`` and ``{{ media.js }}`` separately
don't render import maps unless they add ``{{ media.importmap }}``. This
includes projects overriding the ``extrahead`` block of the admin's
``change_list.html`` without using ``{{ block.super }}``. Code which
builds media objects by copying ``_css_lists`` and ``_js_lists`` would drop the
import map, and code iterating over ``MEDIA_TYPES`` encounters the new
``"importmap"`` type.

``Script`` leaves URLs with other schemes than ``http:`` and ``https:`` alone
(see `Moving assets out of django.forms`_). Such URLs were passed through
``static()`` before, which didn't produce working URLs anyway.

Apart from that it is purely an addition of new features to Django.
Historically, Django has taken care to not break third party apps when there's
no good reason to do so, but given the arguments laid out above, a case can be
made that allowing more than one app to provide and profit from import maps is
a thing which should be possible if not encouraged.


Reference Implementation
========================

There is no implementation of the changes to Django yet.

The proposed API is available for current Django versions in the main branch
of `django-js-asset <https://github.com/feincms/django-js-asset>`__ and will be
released as django-js-asset 5.0, probably after alpha or preview releases which
are only installed when requested explicitly. django-js-asset 5.0 will follow
this DEP as it evolves. As described above, having this functionality in core
would allow everyone to start using import maps in their apps and be sure that
the maps are handled, merged and rendered correctly and consistently.

django-js-asset isn't a reference implementation of the changes to Django
though, since it has to work with Django's existing ``Media``. It ships a
``js_asset.Media`` subclass which supports the ``importmap=`` argument and
merges and renders the import maps. Plain ``Media`` objects have to be wrapped
using ``js_asset.Media.from_media()`` for that. Widgets can't use
``class Media`` for import maps and define
``media = js_asset.Media(importmap=..., js=[...])`` instead, and the admin's
``change_list.html`` has to be overridden to render ``{{ media.importmap }}``.

Prior art:

- https://github.com/rails/importmap-rails
- https://github.com/tonysm/importmap-laravel
- https://github.com/dropseed/django-importmap
- https://github.com/betagouv/dj-importmap
- https://github.com/codingjoe/django-esm

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).
