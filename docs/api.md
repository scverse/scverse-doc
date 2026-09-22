# API

`extensions = ["scverse_doc"]` sets up every subextension below; each also works on its own.

```{eval-rst}
.. automodule:: scverse_doc
```

```{toctree}
:hidden:

api/config.md
api/theme.md
api/source.md
api/registry.md
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

Repository links – the navbar icon, “edit this page”, and `[source]` –
from the {ref}`source_* config values <source-options>`, for whichever theme is selected.

## {doc}`api/registry`

```{eval-rst}
.. autosummary::

    registry.packages
    registry.core_packages
    registry.intersphinx
    registry.Package
```
