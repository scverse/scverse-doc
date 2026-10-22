# `scverse_doc.theme`

```{eval-rst}
.. automodule:: scverse_doc.theme
```

(theme-options)=

## Theme options

`html_theme_options` keys this theme adds. Everything else there is
[pydata-sphinx-theme’s](https://pydata-sphinx-theme.readthedocs.io/en/stable/user_guide/layout.html).
The repository links have their own {ref}`config values <source-options>`.

The theme has no navbar: the logo and the whole site’s navigation are in the primary sidebar,
and the remaining controls in the article header (`article_header_start`/`article_header_end`).
Filling any of the `navbar_start`/`_center`/`_end`/`_persistent` lists brings back a top bar,
and setting `html_sidebars` replaces the site navigation – include `scverse-sidebar-nav` to keep it.
`show_nav_level` sets how many levels of that navigation start expanded.

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

```{confval} secondary_accent
:type: str | bool
:default: none

CSS colour for the sidebar captions; a readable shade is derived from it.
`True` takes the package’s second brand colour from the registry, if it has one.
Without one, the captions keep the text colour.
```

```{confval} show_ecosystem_dropdown
:type: bool
:default: `True`

Whether the scverse menu in the page header lists the “scverse packages”.
Without them, it is a plain link to scverse.org.
```
