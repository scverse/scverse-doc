{{ fullname | escape | underline }}

.. currentmodule:: {{ module }}

.. add toctree option to make autodoc generate the pages

.. autoclass:: {{ fullname }}

{% set methods = methods | select("ne", "__init__") | list %}
{#- Inside autoclass, names resolve against the class’s real module, so prefix the class name:
    `objname` can go through a module alias, and bare members break autosummary’s instance attribute fallback. #}
{% set clsname = fullname.split(".") | last %}

{% block attributes %}
{% for item in attributes %}
{% if loop.first %}
    Attributes table
    ~~~~~~~~~~~~~~~~

    .. autosummary::
{% endif %}
       ~{{ [clsname, item] | join(".") }}
{%- endfor %}
{% endblock %}

{% block methods %}
{% for item in methods %}
{% if loop.first %}
    Methods table
    ~~~~~~~~~~~~~

    .. autosummary::
{% endif %}
       ~{{ [clsname, item] | join(".") }}
{% endfor %}
{% endblock %}

{% block attributes_documentation %}
{% for item in attributes %}
{% if loop.first %}
    Attributes
    ~~~~~~~~~~

{% endif %}
    .. auto{{ [fullname, item] | join(".") | member_type }}:: {{ [fullname, item] | join(".") }}
{%- endfor %}
{% endblock %}

{% block methods_documentation %}
{% for item in methods %}
{% if loop.first %}
    Methods
    ~~~~~~~
{% endif %}
    .. automethod:: {{ [fullname, item] | join(".") }}
{%- endfor %}
{% endblock %}
