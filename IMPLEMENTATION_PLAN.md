# Implementation plan: a shared scverse Sphinx theme

Companion to the RFC: what to build, in what order, and what has to be decided first.

## 0. Ground truth (verified against local checkouts, 2026-07-26)

### 0.1 `scanpydoc` is what this supersedes

`scanpydoc` (0.15.2) is replaced, not extended. Phil authored it and can relicense anything worth porting.

Theme usage today:

| Theme | Packages |
| --- | --- |
| `scanpydoc` (to be retired) | anndata, scanpy, pertpy, ehrapy, ehrdata, rapids_singlecell |
| `sphinx_book_theme` | annbatch, spatialdata, spatialdata-plot, decoupler, scvi-tools, scportrait, pytometry, cookiecutter default |
| `furo` | cellrank, hv-anndata |
| `sphinx_rtd_theme` | squidpy |

Four themes in use, not two as the RFC states.

Five of the six scanpydoc packages depend on its **extensions**, so migration is not just `html_theme`:

| Package | What it imports | Migration cost beyond the theme |
| --- | --- | --- |
| anndata | `scanpydoc` umbrella (before `sphinx.ext.linkcode`), `qualname_overrides` | `linkcode_resolve` + type-alias remapping replacements |
| scanpy | same, plus local `git_ref` ext ordered before `rtd_github_links` | same, plus its own extension ordering |
| rapids_singlecell | `scanpydoc` umbrella | same |
| pertpy | `scanpydoc.elegant_typehints` | type-annotation rendering |
| ehrdata | `scanpydoc.elegant_typehints`, `scanpydoc.definition_list_typed_field` | as above, plus param-field rendering |
| ehrapy | theme only | theme swap only |

Feature surface needing a replacement:

| scanpydoc capability | Replacement | Home |
| --- | --- | --- |
| `rtd_github_links` | a `linkcode_resolve` factory taking `repo` + `ref` | scverse-doc |
| `elegant_typehints` / `qualname_overrides` | reconcile against `sphinx-autodoc-typehints` (already a dep) and `scverse_misc.sphinx_ext`; implement only the gaps | scverse-misc, if anywhere |
| `definition_list_typed_field` | CSS on pydata's default field rendering; directive only if CSS can't | scverse-doc (CSS) |
| `autosummary_generate_imported` | check whether current Sphinx covers it, else reimplement | scverse-misc |
| `release_notes` | unused by anndata/scanpy docs | drop |
| Algolia docsearch + RTD search shim | pydata ships its own search UI | drop |
| `accent_color` theme option | superseded by the registry-driven accent (§2, Layer 3) | scverse-doc |
| `testing.py` helpers | use `sphinx.testing` | drop |

Port existing implementations by default; rewrite only where the new architecture wants something different.

### 0.2 Brand tokens are not TBD

`scverse.github.io/assets/main.scss` is the de facto source of truth:

- Primary `#4557c4`. Gradient `#262fb5 → #74c8fa` (135°), hover variant `#74c8fa → #d4ac00`.
- Neutrals: `#333333` (headers), `#555555` (nav/secondary), `#777777` (muted), `#f0f0f0` / `#e0e0e0` / `#f5f5f5` (tiles/footer), `#f9f9f9` + `#333333` (inline code).
- Per-package accents: anndata `#e5864b`, scanpy `#de367b` (and `#e05559`), mudata `#4ab274`, muon `#6cf1a1`, spatialdata `#40a9ff`, squidpy `#969dea`, scirpy `#da347f`, scvi-tools `#fbb822`.
- Body typeface **Inter** (variable, self-hosted at `static/fonts/Inter/`); Nunito also vendored.
- Logos/favicons: `public/img/icons/*.svg`, `public/img/favicon/` (incl. `site.webmanifest`, `safari-pinned-tab.svg`).

The website has **zero** `prefers-color-scheme` rules, so the dark palette is new design work.

### 0.3 A package registry already exists in two places

- `scverse/ecosystem-packages` – 80 entries as `packages/<Name>/meta.yaml`, JSON-Schema validated, with `documentation_home`, `tutorials_home`, `project_home`, `install`, `license`, `tags`.
- `scverse.github.io/content/packages/_index.md` – Hugo TOML front matter for core packages (`datastructures`, `frameworks`) with `name`, `url`, `img`, `details`, per-package links.

A hand-maintained `_registry.py` would be a third source of truth; generate it from these instead.

### 0.4 `scverse-misc` already owns docstring semantics

`scverse_misc.sphinx_ext` does autodoc/napoleon docstring rewriting (deprecations, settings objects, namespace accessors, prose `Returns:`) and injects `templates_path` with `autosummary/class.rst` and `autosummary/module.rst`. It overlaps `scanpydoc.elegant_typehints` and `sphinx_autodoc_typehints`, and does no theming, chrome, or intersphinx.

Boundary to keep: `scverse-misc` owns API-reference semantics, this package owns theme, chrome, config, registry.

### 0.5 Per-package customisation is small

Hand-written CSS, excluding build output: anndata 0 lines, annbatch 4, scanpy 5, spatialdata 12, decoupler 14, pertpy 100, ehrapy 111, scvi-tools 152. Template overrides: only scvi-tools (1 file).

The expensive part is `conf.py` logic and local extensions: scanpy 10 local extension modules + 303-line `conf.py`, scvi-tools 349 lines, anndata 222 lines + 3 local extensions.

## 1. Decisions required before writing code

D1 and D2 are settled; D0 and D4 need an answer; D3 is a rule the implementation must hold to.

Not decisions, just constraints:

- `scanpydoc` is never a dependency of this package, and the migration guide tells packages to *remove* it. Two themes installed side by side makes entry-point resolution ambiguous.
- `pydata-sphinx-theme` 0.15.4 and `sphinx-book-theme` 1.1.4 are both BSD-3-Clause, so borrowing with attribution is fine.

### D0 – Name and home of the artifact

Repo is `scverse-doc` / `scverse_doc`; the RFC calls the artifact `scverse-sphinx-theme`.

Recommendation: keep the repo as the home for theme + authoring guide + registry, publish the distribution as **`scverse-sphinx-theme`** with import package `scverse_sphinx_theme` and `html_theme = "scverse"`. Matches `pydata-sphinx-theme` / `sphinx-book-theme` naming and is discoverable on PyPI. Renaming is free now (one commit), expensive after the first release.

### D1 – Relationship to `scanpydoc` – **settled**

Greenfield replacement, one direction. No shim, no absorption, no dependency either way. See §0.1.

### D2 – Base theme – **decided: `pydata-sphinx-theme`** (RFC option B)

- `sphinx-book-theme` 1.1.4 sits on `pydata-sphinx-theme` 0.15.4 and lags it. Every pydata feature the RFC wants (top navbar, header dropdowns, announcement bar, version switcher) arrives through a layer whose model – one book, one left rail – is the wrong IA for "one ecosystem, many packages". Two upstreams instead of one, the slower one extra.
- Continuity for the six book-theme-via-scanpydoc packages is real but outweighed: the design is a rebrand anyway (new tokens, new dark mode).
- Phil's experience: working directly against pydata was preferable.
- Cost: week one is slightly harder, since book-theme defaults (left rail, page chrome, repository buttons) must be composed from pydata's `navbar_*` / `footer_*` lists. One-time, lands in M1/M4.
- Risk: pydata 0.15 → current has churn in template partial names, and we hold two overrides (§2, Layer 1). Covered by the weekly upstream-drift build (§6).

Theme option names differ (`repository_url` / `use_repository_button` / `path_to_docs` are book-theme; pydata uses `use_edit_page_button` plus `html_context` GitHub keys, `icon_links`, `navbar_*`, `switcher`), so the eight book-theme packages don't migrate as a no-op diff either. Hence D3.

### D3 – Packages must not touch base-theme options

The config layer is an abstraction boundary. Packages declare intent (`package=`, `repo=`, `accent=`); the theme translates that into whatever the base theme wants. If packages set `html_theme_options` themselves, a base-theme bump is N pull requests again.

Enforcement: the theme warns (and fails under `-W`) on any `html_theme_options` key it owns.

### D4 – Token source of truth

Options: vendor tokens here and sync from the website, or publish a `scverse-brand` token artifact (JSON + CSS) both consume.

Recommendation: **vendor with a generator script and a test** – `scripts/sync_brand_tokens.py` reads `main.scss`, emits `tokens.json` + `_tokens.css`; a test fails on divergence. Extract a separate artifact only if the website team wants to consume it back.

## 2. Architecture

### Layer 1 – Theme

Sphinx theme registered via `[project.entry-points."sphinx.html_themes"]`, so `html_theme = "scverse"` resolves after install. `theme.conf` inherits `pydata_sphinx_theme`. Brand values live in `_tokens.css` as custom properties, mapped onto pydata's `--pst-*` variables in `scverse.css`; the dark palette overrides *tokens only*, never component rules.

Template overrides cost maintenance across pydata releases, so keep two: an ecosystem-dropdown partial and a footer partial. Everything else goes through `html_theme_options` component lists (`navbar_start`, `navbar_center`, `navbar_end`, `footer_start`, `footer_center`).

### Layer 2 – Config

An importable module. `conf.py` is exec'd as a module namespace, so: a function returning a dict of config values, with every piece individually importable.

```python
# docs/conf.py – target end state
from scverse_sphinx_theme import setup_docs

globals().update(
    setup_docs(
        package="pertpy",  # name, version, accent, logo resolved from the registry
        repo="scverse/pertpy",
        intersphinx_extra=["scanpy", "muon"],
    )
)
```

```python
# escape hatch, same building blocks
from scverse_sphinx_theme import config

extensions = [*config.EXTENSIONS, "sphinxcontrib.bibtex"]
html_theme = "scverse"
html_theme_options = config.theme_options(repo="scverse/pertpy", accent="#da347f")
intersphinx_mapping = config.intersphinx("core", "scanpy")
```

Not an extension injecting defaults at `config-inited`: Sphinx has already applied `conf.py` by then, so "default here, override there" requires diffing against Sphinx defaults and misfires when a package legitimately sets a default value. Use an extension only for build hooks (registry-driven navbar, `switcher.json` emission, asset injection, convention linter).

### Layer 3 – Registry

`registry.json` is generated package data, built by `scripts/build_registry.py` from `scverse/ecosystem-packages` (`packages/*/meta.yaml`) and `scverse.github.io/content/packages/_index.md`, with hand-maintained overrides only for accents and inventory URLs that can't be derived. One dict drives the navbar dropdown, the per-package accent, and `intersphinx_mapping`.

- Do **not** default to intersphinx against all 80 ecosystem packages; each is a network fetch per build. `intersphinx()` returns a curated core set (python, numpy, scipy, pandas, matplotlib, anndata, mudata, scanpy, plus the caller's declared extras); everything else opt-in by name.
- Nightly CI resolves every `objects.inv` in the registry and opens an issue on failure. That's what closes RFC problem #3.

### Layer 4 – Conventions, with teeth

Ship an opt-in Sphinx extension emitting warnings (so `-W` enforces where wanted) for: missing required top-level pages, top-level toctree order deviating from canonical, custom admonition titles, theme-owned `html_theme_options` keys, and cards whose icon doesn't match the concept map. Plus a reference `index` + kitchen-sink page in this repo's docs.

### Accent accessibility

Existing per-package accents can't be link colours: `#6cf1a1` (muon) and `#fbb822` (scvi-tools) fail WCAG AA against white, several fail against dark.

Token contract: the raw accent is for decorative/structural surfaces only (hero, active-nav underline, badges, card top-borders); links and text use a *derived* pair of shades, one light-safe, one dark-safe, computed from the accent. A unit test computes contrast for every registry accent in both modes and fails below 4.5:1. Cheap now, impossible to retrofit once packages ship accents.

## 3. Repo layout

```
scverse-doc/
├── pyproject.toml                       # dist: scverse-sphinx-theme; entry point sphinx.html_themes
├── src/scverse_sphinx_theme/
│   ├── __init__.py                      # setup_docs(), setup(), re-exports
│   ├── config.py                        # EXTENSIONS, MYST_*, NAPOLEON_*, theme_options(), intersphinx()
│   ├── registry.py                      # loads registry.json; Package dataclass; accents; inventories
│   ├── registry.json                    # GENERATED – do not hand-edit
│   ├── switcher.py                      # switcher.json contract + writer
│   ├── conventions.py                   # opt-in convention linter (Sphinx warnings)
│   ├── _ext.py                          # build-time hooks: navbar dropdown, assets, switcher
│   └── theme/scverse/
│       ├── theme.conf                   # inherit = pydata_sphinx_theme
│       ├── components/                  # ecosystem-dropdown.html, scverse-footer.html
│       └── static/
│           ├── _tokens.css              # GENERATED from the website's main.scss
│           ├── scverse.css              # token -> --pst-* mapping, component overrides
│           ├── scverse-dark.css         # dark token overrides only
│           ├── fonts/                   # Inter (variable), subset
│           ├── logos/                   # scverse marks (light/dark) + per-package marks
│           └── favicons/
├── scripts/
│   ├── sync_brand_tokens.py             # main.scss  -> _tokens.css + tokens.json
│   ├── build_registry.py                # ecosystem-packages + website TOML -> registry.json
│   └── migrate_conf.py                  # best-effort conf.py rewriter for migrations
├── docs/                                # dogfoods the theme; authoring guide + kitchen sink
└── tests/
    ├── roots/                           # fixture doc trees (minimal, full, deviant)
    ├── test_build.py                    # -W builds, HTML assertions
    ├── test_tokens.py                   # contrast + drift-vs-website
    └── test_registry.py                 # schema, and (nightly) inventory reachability
```

## 4. Milestones

Focused days, one implementer, review latency in parallel.

### M0 – Decisions and skeleton (0.5 d + discussion latency)

D0 and D4 resolved in the RFC thread. Repo renamed if D0 says so, dependency set trimmed (the cookiecutter scaffold pulls `anndata` and `session-info2`, neither needed by a theme), theme entry point registered.
Exit: `sphinx-build` of `tests/roots/minimal` succeeds with no warnings.

### M1 – Tokens and dark mode (2 d)

`sync_brand_tokens.py`, `_tokens.css`, the `--pst-*` mapping, Inter subsetting and self-hosting, derived-accent contrast machinery, hand-designed dark palette.
Exit: kitchen-sink page renders in light and dark; contrast test green for every registry accent.

### M2 – Config layer (2 d)

`EXTENSIONS` and MyST/napoleon/typehints/copybutton/opengraph defaults lifted from the cookiecutter `conf.py` and reconciled against what anndata/scanpy/pertpy set. `setup_docs()`, `theme_options()`, theme-owned-key warning.
Exit: the cookiecutter's ~40-line block reduces to the ~8-line call, byte-identical HTML for a fixture tree.

### M2.5 – Replacements for the scanpydoc extensions (3–4 d)

The difference between "eight packages can migrate" and "all fourteen can".

- `linkcode_resolve` factory driven by `repo`, RTD-aware, replacing `rtd_github_links` (anndata, scanpy, rapids_singlecell block on this).
- Type-annotation rendering: measure what `sphinx-autodoc-typehints` + `scverse_misc.sphinx_ext` already produce for anndata's and scanpy's `qualname_overrides` cases, implement only the residue. May be a config recipe rather than code.
- Param-field rendering: try CSS-only before writing a `definition_list_typed_field` equivalent.
- Decide `autosummary_generate_imported` (reimplement in `scverse-misc`, or confirm Sphinx covers it).

Exit: a fixture tree exercising all four renders correctly; pertpy + ehrdata build with `scanpydoc` uninstalled.

### M3 – Registry (2 d)

`build_registry.py`, `registry.json`, `intersphinx()` with curated-core default, registry-driven navbar dropdown, nightly inventory-reachability workflow.
Exit: dropdown lists core + ecosystem entries; a deliberately broken inventory URL fails the nightly job.

### M4 – Chrome (2 d)

Footer (NumFOCUS, governance, license), announcement banner wired to a single governance-controlled URL published by `scverse.github.io` (pydata fetches this client-side, so the endpoint needs permissive CORS), `use_edit_page_button` derived from `repo`, `switcher.py`.

Version switcher: do **not** call the RTD API during the Sphinx build. Ship a scheduled/on-release GitHub workflow (delivered via the cookiecutter) that regenerates `switcher.json` and commits it.
Exit: switcher works on an RTD preview build of this repo.

### M5 – Conventions and reference docs (2 d)

`conventions.py` warnings, authoring guide, reference `index` hero and API overview page, octicon/badge maps.
Exit: `tests/roots/deviant` produces exactly the expected warning set.

### M6 – Pilots (3–4 d, mostly review latency)

Ordering in §5.
Exit: two pilot packages merged and rendering; migration guide written from what actually broke.

### M7 – Cookiecutter and rollout (1 d + adoption latency)

`cookiecutter-scverse`'s `conf.py`, `pyproject.toml` doc deps, and the `switcher.json` workflow updated; `cruft` propagates to opted-in repos. The generated `pyproject.toml` must not carry `scanpydoc`.

## 5. Rollout order (revised)

Not anndata first: 222-line `conf.py`, 3 local extensions, a curated `nitpick_ignore`, highest traffic of any scverse site.

| Wave | Packages | Why | Rough effort each |
| --- | --- | --- | --- |
| 1 (pilot) | `annbatch`, `pertpy` | annbatch is cookiecutter-native, book theme, 4 lines of CSS – proves the ecosystem path. pertpy is on scanpydoc but only for `elegant_typehints`, large, has notebook tutorials, maintained by the RFC author – proves the leaving-scanpydoc path cheaply. | 0.5 d / 1–2 d |
| 2 | `spatialdata`, `spatialdata-plot`, `decoupler`, `scportrait`, `pytometry`, `scvi-tools` | Book theme, ≤152 lines of CSS, no scanpydoc, mechanical. | ~0.5 d each (scvi-tools ~1 d) |
| 3 | `ehrapy`, `ehrdata`, then `anndata`, `scanpy`, `rapids_singlecell` | Leaving scanpydoc. ehrapy is theme-only; ehrdata needs two extension replacements; anndata/scanpy/rapids_singlecell need the full M2.5 set plus bespoke `conf.py` logic (scanpy: 10 local extensions, `git_ref` ordering dependency on `rtd_github_links`). Blocked on M2.5. | 0.5 d / 1 d / 2–3 d each |
| 4 | `squidpy` (rtd theme), `cellrank` + `hv-anndata` (furo) | Different base theme; nav structure and CSS assumptions don't carry over. | 2–3 d each |

Write `scripts/migrate_conf.py` *during* wave 2, from wave 1's diffs.

## 6. Testing and CI

- **Build tests.** Fixture roots under `tests/roots/` built with `-W` via `sphinx.testing`: theme resolves, expected CSS/JS injected, navbar dropdown contains registry entries, `switcher.json` emitted, `intersphinx_mapping` shape, accent override applied, theme-owned-key warning fires.
- **Token tests.** Contrast ratios for all derived accents in both modes; drift check against `main.scss`.
- **Registry tests.** Schema validation per commit; `objects.inv` reachability nightly only (network).
- **Upstream-drift job.** Weekly build against `pydata-sphinx-theme` `main` – template partial renames are the main breakage risk for the two overrides.
- **Visual regression (optional, after M5).** Playwright screenshots of the kitchen-sink page in light and dark, compared per PR.

## 7. Risks

| Risk | Mitigation |
| --- | --- |
| Wave 3 stalls because scanpydoc extension replacements are missing | M2.5 delivers them before wave 3 starts |
| pydata option/partial churn | D3 boundary + weekly upstream-drift build + only two template overrides |
| Per-package accents fail contrast | Derived accent pair + contrast test in M1 |
| Docs/website token drift | Generator + drift test, not hand-copied hex values |
| Build slowdown from many intersphinx inventories | Curated core default, opt-in extras, `intersphinx_timeout`, cached inventories in CI |
| `nitpicky = True` plus new cross-package links surfaces a wave of warnings | Migration guide includes a `nitpick_ignore` triage step; don't ship registry-wide intersphinx and nitpicky enforcement in one PR |
| Dark mode is net-new design | Budgeted in M1; needs a design review |
| Adoption stalls after wave 2 | Cookiecutter default (M7); conventions linter makes drift visible; waves 3–4 encouraged, not forced |

## 8. Suggested RFC edits

1. Add a "Prior art: what replaces `scanpydoc`" section: six packages use it, five use its *extensions*, replacing those is scoped work.
2. Replace "final hex values TBD from the official logo" with the palette extracted from `main.scss`; note the dark palette is the only undecided part.
3. Correct the drift inventory: four themes, including `sphinx_rtd_theme` (squidpy) and `furo` (cellrank, hv-anndata).
4. State the registry as derived from `scverse/ecosystem-packages` + the website's package TOML, not a new hand-maintained dict.
5. Add D3 (packages never set base-theme options) to the Approach section.
6. Add the accent-contrast constraint to the design-tokens section; reframe `--scverse-color-accent` as decorative-only with derived link shades.
7. Under Alternatives, reference the conventions linter as the enforcement mechanism.
