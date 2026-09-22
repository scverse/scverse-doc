# `scverse_doc.theme`

```{eval-rst}
.. automodule:: scverse_doc.theme
```

(theme-options)=

## Theme options

`html_theme_options` keys this theme adds. Everything else there is
[pydata-sphinx-theme’s](https://pydata-sphinx-theme.readthedocs.io/en/stable/user_guide/layout.html).
The repository links have their own {ref}`config values <source-options>`.

```{confval} package
:type: str
:default: `project`

The registry name to look the accent and the dropdown’s current entry up under.
```

```{confval} accent
:type: str
:default: the registry accent, else the scverse primary

CSS colour for decorative surfaces; link and text shades are derived from it.
```

```{confval} show_ecosystem_dropdown
:type: bool
:default: `True`

Whether the navbar carries the “scverse packages” dropdown.
```
