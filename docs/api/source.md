# `scverse_doc.source`

```{eval-rst}
.. automodule:: scverse_doc.source
```

(source-options)=

## Configuration

```{confval} source_repository
:type: str
:default: `""`

The repository URL, e.g. `"https://gitlab.com/owner/name"`.
Empty means no repository links at all.
```

```{confval} source_branch
:type: str
:default: `$READTHEDOCS_GIT_IDENTIFIER`, else `"main"`

The ref the links point at.
Read the Docs pull request builds fall back to the default, since they identify by PR number.
```

```{confval} source_directory
:type: str
:default: `"docs"`

Where the documentation sources live in the repository.
```

```{confval} source_code_directory
:type: str
:default: `"src"`

Where the importable code lives in the repository, for the `[source]` links.
Set it to `""` for a flat layout.
```

```{confval} source_provider
:type: str
:default: inferred from the host

Which forge’s URL layout the repository follows:
`"github"`, `"gitlab"` or `"bitbucket"`.
Inferring it works for the hosted instances and for self-hosted ones whose host
name contains the forge’s (`gitlab.example.org`); name it for anything else.
An unknown forge still gets the navbar icon, just no per-page links.
```

## What each theme gets

| Theme | Reads |
| --- | --- |
| `pydata-sphinx-theme`, and so {doc}`ours <theme>` | `html_context`’s `{provider}_user`/`_repo`/`_version`/`_url` and `doc_path`, plus `use_edit_page_button` |
| `sphinx_rtd_theme` | the same, plus `display_{provider}`, `{provider}_host` and `conf_py_path` |
| `furo`, and anything else on `sphinx-basic-ng` | the `source_repository`/`source_branch`/`source_directory` theme options, plus `display_{provider}` for its footer icon – which it shows on Read the Docs only |
| `sphinx-book-theme` | the `repository_url`/`repository_branch`/`repository_provider`/`path_to_docs` theme options, plus `use_repository_button`, `use_source_button` and `use_issues_button` |

Only the options a theme declares are written; a theme that declares none of them –
`alabaster`, say – is left alone. Anything `conf.py` set itself wins.

## `[source]` links

Listing {mod}`sphinx.ext.linkcode` is enough; the resolver is filled in:

```python
extensions = ["scverse_doc.source", "sphinx.ext.linkcode"]

source_repository = "https://github.com/scverse/pertpy"
# no need to define `linkcode_resolve`
```

A `linkcode_resolve` of your own still wins.
