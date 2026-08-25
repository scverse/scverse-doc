# Kitchen sink

Every component the theme styles, on one page, so a change to
[`scverse.css`](https://github.com/scverse/scverse-doc/blob/main/src/scverse_doc/theme/scverse/static/styles/scverse.css)
can be eyeballed in both colour schemes. The navbar, ecosystem dropdown and footer are on this page
like on any other – switch the theme with the toggle in the navbar.

## Text

Body copy with **bold**, *italic*, `inline literal` (the default role), an
[external link](https://scverse.org), an [internal one](api.md), a footnote[^fn] and a
cross-reference to {func}`~scverse_doc.registry.intersphinx`.

[^fn]: Footnotes land here.

### Third level

#### Fourth level

Inline maths $e^{i\pi} = -1$ and a block:

$$
\operatorname{AA}(c_\text{fg}, c_\text{bg}) \geq 4.5
$$

### Inline roles

Press {kbd}`Ctrl` + {kbd}`K`, hit {guilabel}`Search`, then {menuselection}`View --> Theme --> Dark`.
Run {command}`hatch run docs:build`, which writes {file}`docs/_build/html/{page}.html`, prints
{samp}`build succeeded`, and is what {abbr}`CI (continuous integration)` calls. A {dfn}`token` is a
custom property; H{sub}`2`O and x{sup}`2` also render.

## Lists

- Bullet
- Bullet
  - Nested

1. Numbered
2. Numbered

Definition list
: Enabled through the `deflist` MyST extension.

Field and option lists and `hlist` are docutils-only, so they need `eval-rst`:

```{eval-rst}
:Field: A field list entry.
:Another: A second one.

-W                     Turn warnings into errors.
-D <setting=value>     Override a ``conf.py`` value.
--keep-going           A long option.

.. hlist::
   :columns: 3

   * anndata
   * mudata
   * scanpy
   * scirpy
   * scvi-tools
   * squidpy
```

## Admonitions

```{note}
A note, in the theme's border and surface tokens.
```

```{warning}
A warning.
```

```{seealso}
A cross-reference box.
```

```{tip}
A tip.
```

```{important}
Something important.
```

```{hint}
A hint.
```

```{attention}
Pay attention.
```

```{caution}
Be careful.
```

```{danger}
Danger.
```

```{error}
An error.
```

```{admonition} A custom title
:class: note

An admonition with its own title, styled from the `note` class.
```

:::{dropdown} A collapsed dropdown
Body of the dropdown.
:::

## Versions

```{versionadded} 0.1.0
This page.
```

```{versionchanged} 0.2.0
Grew the badge section.
```

```{deprecated} 0.3.0
Nothing yet.
```

## Structure

```{rubric} A rubric
```

> A block quote, for text lifted from somewhere else.

:::{topic} A topic
A boxed aside that flows with the text.
:::

:::{sidebar} A sidebar
Floats beside the body copy.
:::

```{eval-rst}
| A line block,
|     kept as broken.

.. glossary::

   token
      A CSS custom property in ``_tokens.css``.

   accent
      The per-package colour, decorative only.
```

## Code

```{code-block} python
:caption: With a caption and a copy button.

from scverse_doc import intersphinx

mapping = intersphinx() | {"sphinx": ("https://www.sphinx-doc.org/en/master/", None)}
```

```console
$ hatch run docs:build
```

```{code-block} python
:linenos:
:emphasize-lines: 2

first = "plain"
second = "emphasised"
third = "plain"
```

```pycon
>>> from scverse_doc import registry
>>> registry.packages["scanpy"].accent
'#de367b'
```

## Table

| Token                              | Role                                |
| ---------------------------------- | ----------------------------------- |
| `--scverse-color-accent-text`      | Links and text, contrast-checked    |
| `--scverse-color-accent-decorative`| Underlines and surfaces             |
| `--scverse-radius`                 | Shared component geometry           |

## Cards

::::{grid} 1 2 2 3
:gutter: 2

:::{grid-item-card} Plain card
Title colour comes from `--pst-heading-color`.
:::

:::{grid-item-card} Linked card
:link: api.md

Hover it: the title switches to the accent, the card lifts.
:::

:::{grid-item-card} With a footer
Body.
+++
Footer.
:::
::::

## Badges and buttons

{bdg-primary}`primary` {bdg-secondary}`secondary` {bdg-info}`info`
{bdg-warning}`warning` {bdg-danger}`danger`

`primary` is the scverse brand colour, `secondary` the package accent – so the two coincide
whenever a package does not set `accent` and inherits the brand colour as its default. To see the
accent-driven parts of the theme, build with one:

```console
$ hatch run docs:build -D html_theme_options.accent=#de367b
```

```{button-link} https://scverse.org
:color: primary
A button
```

## Tabs

::::{tab-set}
:::{tab-item} First
Content of the first tab.
:::
:::{tab-item} Second
Content of the second tab.
:::
::::
