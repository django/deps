DEP : Multiline Template Tags
=============================

:Created: 2014-04-16
:Author: Curtis Maloney
:Status: Draft

Several people have asked for the django template language (DTL) to support newlines within template tags.

Arguments for
-------------

Several examples were given, such as:

- Form rendering tool which accepted many arguments in a block tag.
- Thumbnailing tools which take many arguments.
- Multi-clause {% if %} tags.
- "practicality beats purity"
- ``{% blocktrans %}``

  Consider a basic case:

  .. code-block:: html

    {% blocktrans with adjective=widsom.adjective animal=wisdom.animal %}The {{ adjective }} {{animal}} jumps over the lazy dog, lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."{% endblocktrans %}

  (NB it causes a great deal of pain to have line breaks inside {% blocktrans %}; advice originally from Jacob Burch's "Gringo's Guide to Internationalisation" at DC 2012)

  If nothing else, multi-line template tags would allow the following (with variables on their own line) instead:

  .. code-block:: html

    {% blocktrans with adjective=widsom.adjective animal=wisdom.animal 
    %}The {{ adjective }} {{animal}} jumps over the lazy dog, lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."{% endblocktrans %}

- ```{% url %}```

  .. code-block:: html

    {% url 'workshop_manuscript_detail' workshop_slug=workshop.slug slug=manuscript.slug as url %}

  versus

  .. code-block:: html

    {% url 'workshop_manuscript_detail' 
      workshop_slug=workshop.slug 
      slug=manuscript.slug as url %}

- More familiar pattern for users of HTML, who can already format long HTML elements this way.

Arguments against
-----------------

DTL is intended to discourage putting business logic in templates. Allowing long,
complex conditions and such in templates does not work to this goal.

Sample implementation
---------------------

I have created a sample implementation based on work I'd done for another 
template engine.  It is available `here <https://github.com/funkybob/django/compare/multiline-templates>`_
