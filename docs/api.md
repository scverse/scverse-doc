# API

`extensions = ["scverse_doc"]` sets up every subextension below; each also works on its own.

```{eval-rst}
.. automodule:: scverse_doc
```

```{toctree}
:hidden:

api/config.rst
api/theme.md
api/source.md
api/registry.rst
api/autodoc.rst
api/napoleon.rst
api/math_core.rst
api/release_notes.rst
api/typed_fields.rst
api/xref_overrides.rst
```

## {doc}`api/config`

```{eval-rst}
.. autosummary::

    config.EXTENSIONS
    config.MYST_ENABLE_EXTENSIONS
    config.DEFAULTS
```

## {doc}`api/theme`

Registers the theme and its {ref}`theme options <theme-options>`.
Selecting it with `html_theme = "scverse"` is enough on its own –
it is a registered Sphinx theme, so it needs no `extensions` entry.

## {doc}`api/source`

Repository links – the header icon, “edit this page”, and `[source]` –
from the {ref}`source_* config values <source-options>`, for whichever theme is selected.

## {doc}`api/registry`

```{eval-rst}
.. autosummary::

    registry.packages
    registry.core_packages
    registry.intersphinx
    registry.Package
```

## {doc}`api/autodoc`

Autosummary templates for module and class pages,
and private bases left out of `:show-inheritance:`.

## {doc}`api/napoleon`

Prose `Returns` sections in NumPy-style docstrings.

## {doc}`api/math_core`

Math rendered to MathML at build time, via [math-core](https://github.com/tmke8/math-core) – no JavaScript needed.

## {doc}`api/release_notes`

A `release-notes` directive, rendering a directory of per-version files grouped by minor version.

## {doc}`api/typed_fields`

Parameters and attributes rendered as definition lists, like numpydoc.

## {doc}`api/xref_overrides`

An `xref_overrides` config value, redirecting cross-references to objects documented under another name or role.
