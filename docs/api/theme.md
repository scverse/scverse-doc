# `scverse_doc.theme`

```{eval-rst}
.. automodule:: scverse_doc.theme
```

(theme-options)=

## Theme options

`html_theme_options` keys this theme adds. Everything else there is
[pydata-sphinx-theme’s](https://pydata-sphinx-theme.readthedocs.io/en/stable/user_guide/layout.html).

```{confval} package
:type: str
:default: `project`

The registry name to look the accent and the dropdown’s current entry up under.
```

```{confval} repo
:type: str
:default: `""`

`owner/name` on GitHub. Adds the navbar icon and the “edit this page” button.
```

```{confval} branch
:type: str
:default: `$READTHEDOCS_GIT_IDENTIFIER`, else `"main"`

The ref {confval}`repo`’s edit links point at.
Read the Docs pull request builds fall back to the default, since they identify by PR number.
```

```{confval} doc_path
:type: str
:default: `"docs/"`

Where the documentation sources live in {confval}`repo`.
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
