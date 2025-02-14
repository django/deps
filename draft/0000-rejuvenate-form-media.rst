======================
DEP XXXX: Rejuvenate form media
======================

:DEP: XXXX
:Author: Matthias Kestenholz, Thibaud Colas
:Implementation Team: You? People in the `forum thread: Rejuvenating vs deprecating Form.Media <https://forum.djangoproject.com/t/rejuvenating-vs-deprecating-form-media/21285>`_
:Shepherd: You?
:Status: Draft
:Type: Feature
:Created: 2023-12-12
:Last-Modified: 2025-02-14

.. contents:: Table of Contents
   :depth: 3
   :local:

Abstract
========

``forms.Media`` allows Django's forms, widgets and the administration interface to define required CSS and JavaScript assets, collecting the required assets from all widgets on a page, ordering them and outputting the result to the browser.

The functionality has been somewhat neglected since it has been introduced initially, and the question was raised whether `the media object should be rejuvenated or deprecated <https://forum.djangoproject.com/t/rejuvenating-vs-deprecating-form-media/21285>`_. The consensus was that ``forms.Media`` was widely used and seen as useful.  

In the meantime, `object-based Script objects <https://docs.djangoproject.com/en/5.2/topics/forms/media/#script-objects>`_ were introduced to Django adding an easy way to add attributes to script tags. This DEP proposes ways to further enhance ``forms.Media`` so Django projects can more easily leverage the Web standards around asset loading.


Specification
=============

A renewed ``forms.Media`` should take full advantage of the object-based assets functionality.

The ``Script`` implementation is already there.

A new ``Stylesheet`` implementation can be easily added by reusing the existing ``django.forms.widgets.MediaAsset`` class, while preserving the ``media="all"`` default of the existing code:

.. code-block:: python

        class Stylesheet(MediaAsset):
            element_template = '<link href="{path}"{attributes}>'

            def __init__(self, path, **attributes):
                attributes.setdefault("media", "all")
                # Alter the signature to allow src to be passed as a keyword argument.
                super().__init__(path, **attributes)


The current differentiation between CSS and JS assets isn't necessary, instead, assets can be immediately converted into object-based assets and collected in one list. The existing ``_css_lists`` and ``_js_lists`` attributes of ``forms.Media`` are replaced by a single ``_assets_lists`` attribute. This avoids the confusion of allowing to specify the medium for stylesheets both in the dictionary key (``css = {"all": ["style.css"]}``) and also in the object (``Stylesheet("style.css", media="all")``).

Browser support for `importmaps <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/script/type/importmap>`_ has reached baseline in 2023. However, browsers still only support one importmap per page, which means that there has to exist a way to aggregate importmap entries from all sorts of forms, widgets, etc. The ``forms.Media`` class already does something like this, so it could be easily extended to also allow importmap entries:

.. code-block:: python

    @html_safe
    @dataclass(eq=True)
    class ImportMapImport:
        key: str
        value: str
        scope: str | None = None

        def __hash__(self):
            return hash((self.key, self.value, self.scope))

        def __str__(self):
            return ""

The ``forms.Media`` rendering should then be extended to automatically collect importmap entries and produce the appropriate ``<script type="importmap">`` element on the page:

.. code-block:: python

    class Media:
        # ...

        def render(self):
            assets = self.merge(*self._asset_lists)

            importmap = self.render_importmap(
                asset for asset in assets if isinstance(asset, ImportMapImport)
            )

            return mark_safe(
                "\n".join(
                    filter(None, chain([importmap], (asset.__html__() for asset in assets)))
                )
            )

        def render_importmap(self, entries):
            if not entries:
                return ""
            importmap = {"imports": {}}
            for entry in entries:
                if entry.scope:
                    scope = importmap.setdefault("scopes", {}).setdefault(entry.scope, {})
                    scope[entry.key] = entry.value
                else:
                    importmap["imports"][entry.key] = entry.value
            html = json_script(importmap).removeprefix('<script type="application/json">')
            return mark_safe(f'<script type="importmap">{html}')


Deferred functionality
~~~~~~~~~~~~~~~~~~~~~~

This DEP doesn't yet propose a way to add support for the following functionalities, but the groundwork done here would offer a better foundation for adding support for:

- CSP via ``nonce`` attributes
- Automatic ``integrity`` attributes
- Possible postprocessing and/or bundling of assets

And maybe also:

- Preloading / speculative loading
- Resource ordering (see `capo.js <https://rviscomi.github.io/capo.js/>`_)
- Web Components (@Thibaud, I'm not sure I understand this point)


Motivation
==========

Django has supported object-based assets in ``forms.Media`` for several years. Proper support has been added in `#29490 <https://code.djangoproject.com/ticket/29490>`_, however Django hasn't shipped any classes using this facility until recently.

Django 5.2 has introduced support for `object-based JavaScript objects <https://docs.djangoproject.com/en/5.2/topics/forms/media/#script-objects>`_, making it possible to easily add script tags with arbitrary HTML attributes, for example to add ``type="module"``:

.. code-block:: python

    from django import forms

    media = forms.Media(
        js=[forms.Script("module.js", type="module")]
    )

``forms.Media`` can contain arbitrary object-based assets The same doesn't
exist for stylesheets or other asset types.

As an example, the third party package `django-js-asset
<https://pypi.org/project/django-js-asset/>`_ (Disclaimer: I'm the primary
author.) have taken advantage of object-based media for a long time, and ship
objects which allow adding CSS, JavaScript and JSON as media assets.

This section should explain why this DEP is needed. The motivation is critical for DEPs that want to add substantial new features or materially refactor existing ones. It should clearly explain why the existing solutions are inadequate to address the problem that the DEP solves. DEP submissions without sufficient motivation may be rejected outright.

Rationale
=========

This section should flesh out out the specification by describing what motivated
the specific design and why particular design decisions were made.  It
should describe alternate designs that were considered and related work.

The rationale should provide evidence of consensus within the community and
discuss important objections or concerns raised during discussion.

Backwards Compatibility
=======================

Code which directly uses the existing ``_css_lists`` and ``_js_lists`` attributes would have to be changed. Those attributes are not documented, and the leading underscore clearly communicates that they are an implementation detail. They are not part of the public API and we should therefore be able to remove them as discussed above without too much fanfare.

- django-csp-helpers (``CSPAwareMedia``)


Reference Implementation
========================

An experimental implementation supporting importmaps and the discussed unification of object-based media is available here:

https://github.com/matthiask/django-js-asset/compare/mk/importmaps

It even works with relased Django versions, but it doesn't use the ``forms.Script`` class yet, that would have to be changed.



Here are the most fully-fledged implementations so far:

- https://github.com/matthiask/django-js-asset/
- https://github.com/rails/importmap-rails

Other references:

- https://github.com/dropseed/django-importmap
- https://github.com/tonysm/importmap-laravel

TODOs
=====

- Add more possible requirements
- Review https://github.com/wsvincent/awesome-django for packages with form media-related functionality.
- Review https://djangopackages.org/ for packages with form media-related functionality.
- Also update https://github.com/wsvincent/awesome-django with good packages in this category

Copyright
=========

This document has been placed in the public domain per the Creative Commons
CC0 1.0 Universal license (http://creativecommons.org/publicdomain/zero/1.0/deed).
