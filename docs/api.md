# API

`extensions = ["scverse_doc"]` sets up every subextension below; each also works on its own.

```{eval-rst}
.. automodule:: scverse_doc
```

```{toctree}
:hidden:

api/config.md
api/theme.md
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

## {doc}`api/registry`

```{eval-rst}
.. autosummary::

    registry.packages
    registry.core_packages
    registry.intersphinx
    registry.Package
    registry.cache_dir
    registry.build_cache
```
