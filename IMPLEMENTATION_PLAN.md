# Implementation plan: a shared scverse Sphinx theme

Companion to the RFC.
This document says *what* to build, in *what order*, and which decisions have to be made before any code is written.

Everything in "Ground truth" below was verified against locally checked-out repos and installed packages, not assumed.

## 0. Ground truth (verified, 2026-07-26)

### 0.1 `scanpydoc` is what this supersedes, and it is GPL

`scanpydoc` (0.15.2) is `License-Expression: GPL-3.0-or-later`.
This package is MPL-2.0.
**Nothing may be copied from `scanpydoc` — not code, not CSS, not templates, not `theme.conf` values.**
It is being replaced, not extended or absorbed, and the migration is one-directional.

That constraint is load-bearing for the whole plan, so it gets its own section: see [§1.1](#11-clean-room-constraint).

Actual theme usage across locally cloned repos:

| Theme | Packages |
| --- | --- |
| `scanpydoc` (to be retired) | anndata, scanpy, pertpy, ehrapy, ehrdata, rapids_singlecell |
| `sphinx_book_theme` | annbatch, spatialdata, spatialdata-plot, decoupler, scvi-tools, scportrait, pytometry, cookiecutter default |
| `furo` | cellrank, hv-anndata |
| `sphinx_rtd_theme` | squidpy |

So the drift is worse than the RFC states: four themes, not two.
The core/ecosystem split is really "core is on scanpydoc, ecosystem is on the cookiecutter's book theme, plus two outliers".

Critically, those six packages depend on scanpydoc **extensions**, not only its theme, so "migrate off scanpydoc" is much more than changing `html_theme`:

| Package | What it imports | Migration cost beyond the theme |
| --- | --- | --- |
| anndata | `scanpydoc` umbrella (before `sphinx.ext.linkcode`), `qualname_overrides` | needs `linkcode_resolve` + type-alias remapping replacements |
| scanpy | `scanpydoc` umbrella (before `sphinx.ext.linkcode`), `qualname_overrides`, local `git_ref` ext ordered before `rtd_github_links` | same, plus its own extension ordering to unpick |
| rapids_singlecell | `scanpydoc` umbrella | same |
| pertpy | `scanpydoc.elegant_typehints` | type-annotation rendering replacement |
| ehrdata | `scanpydoc.elegant_typehints`, `scanpydoc.definition_list_typed_field` | as above, plus param-field rendering |
| ehrapy | theme only | theme swap only |

Feature surface that therefore needs a clean-room replacement, with a proposed home for each:

| scanpydoc capability | Replacement | Home |
| --- | --- | --- |
| `rtd_github_links` (source links, RTD-aware) | a `linkcode_resolve` factory taking `repo` + `ref`; the RFC's `repo` value already supplies the input | scverse-doc |
| `elegant_typehints` / `qualname_overrides` | reconcile against `sphinx-autodoc-typehints` (already a dep) and `scverse_misc.sphinx_ext`; implement only the genuine gaps | scverse-misc, if anywhere |
| `definition_list_typed_field` | try CSS on pydata's default field rendering first; only write a directive if CSS cannot get there | scverse-doc (CSS) |
| `autosummary_generate_imported` | small enough to reimplement; check first whether current Sphinx covers it | scverse-misc |
| `release_notes` | not used by anndata or scanpy docs; do not port unless a consumer appears | drop |
| Algolia docsearch options + RTD search shim | pydata ships its own search UI; standardise on it | drop |
| `accent_color` theme option | superseded by the registry-driven accent (§2, Layer 3) | scverse-doc |
| `testing.py` helpers | use `sphinx.testing` directly | drop |

Functionality is not copyrightable and expression is, so each of these is implemented from observed rendered behaviour and public documentation.
See §1.1 for how to keep that defensible.

### 0.2 The brand tokens are not TBD

`scverse.github.io/assets/main.scss` is the de facto brand source of truth:

- Primary: `#4557c4`. Brand gradient: `#262fb5 → #74c8fa` (135°), with a hover variant `#74c8fa → #d4ac00`.
- Neutrals: `#333333` (headers), `#555555` (nav/secondary), `#777777` (muted), `#f0f0f0` / `#e0e0e0` / `#f5f5f5` (tiles/footer), `#f9f9f9` + `#333333` (inline code).
- Per-package accents already exist: anndata `#e5864b`, scanpy `#de367b` (and `#e05559`), mudata `#4ab274`, muon `#6cf1a1`, spatialdata `#40a9ff`, squidpy `#969dea`, scirpy `#da347f`, scvi-tools `#fbb822`.
- Body typeface: **Inter** (variable font, self-hosted at `static/fonts/Inter/`); Nunito is also vendored.
- Logos and favicons: `public/img/icons/*.svg` (per-package marks, `scverse_bw_logo.svg`, `scverse_blue_logo.svg`) and `public/img/favicon/` (full set incl. `site.webmanifest`, `safari-pinned-tab.svg`).

Two consequences.
The RFC's "final hex values TBD from the official logo" open question can be closed by extraction rather than design.
And the website has **zero** `prefers-color-scheme` rules, so the dark palette is genuinely new design work that no upstream source can supply.

### 0.3 A package registry already exists in two places

- `scverse/ecosystem-packages` — 80 entries as `packages/<Name>/meta.yaml`, JSON-Schema validated, each with `documentation_home`, `tutorials_home`, `project_home`, `install`, `license`, `tags`.
- `scverse.github.io/content/packages/_index.md` — Hugo TOML front matter listing core packages (`datastructures`, `frameworks`) with `name`, `url`, `img`, `details`, and per-package links.

A hand-maintained `_registry.py` would be a **third** source of truth for the same data.
It should be generated from these two instead.

### 0.4 `scverse-misc` already owns docstring semantics

`scverse_misc.sphinx_ext` does autodoc/napoleon docstring rewriting (deprecations, settings objects, namespace accessors, prose `Returns:`) and injects `templates_path` with `autosummary/class.rst` and `autosummary/module.rst`.
It overlaps with `scanpydoc.elegant_typehints` and `sphinx_autodoc_typehints`.
It does **no** theming, chrome, or intersphinx.
That is a clean boundary to keep: `scverse-misc` owns *API-reference semantics*, the new package owns *theme, chrome, config, and registry*.

### 0.5 Per-package customisation is small, which makes migration cheap

Hand-written CSS, excluding build output: anndata 0 lines, annbatch 4, scanpy 5, spatialdata 12, decoupler 14, pertpy 100, ehrapy 111, scvi-tools 152.
Template overrides: only scvi-tools has one (1 file).
The expensive part is not CSS, it is `conf.py` bespoke logic and local extensions: scanpy has 10 local extension modules and a 303-line `conf.py`, scvi-tools 349 lines, anndata 222 lines with 3 local extensions.

## 1. Decisions required before writing code

D1 and D2 are settled and recorded here for the RFC; D0 and D4 still need an answer, and D3 is a rule the implementation has to hold to.
Each of these invalidates work done under the wrong assumption, so they come before code.

### 1.1 Clean-room constraint

Settled, not open: `scanpydoc` is GPL-3.0-or-later, this package is MPL-2.0, and there is no compatible path for reuse.
The rules that follow from that:

- No file, snippet, selector, or template is copied from `scanpydoc`, and it is never a runtime, build, test, or docs dependency of this package.
- Replacements are written from **rendered output and public documentation** — what the HTML looks like, what the documented config values do — not from reading its source and transcribing.
- Anyone implementing a replacement for a capability in the §0.1 table should say so in the PR description ("reimplemented from documented behaviour of X"), which costs nothing now and is the only cheap moment to establish provenance.
- Base themes are fine to build on and to borrow from with attribution: `pydata-sphinx-theme` 0.15.4 and `sphinx-book-theme` 1.1.4 are both BSD-3-Clause.
- The migration guide must tell packages to *remove* `scanpydoc` from their doc dependencies, not to keep it alongside. Two themes installed side by side is how the entry-point resolution gets confusing and how a "migrated" package quietly keeps rendering GPL CSS.

This also means the six scanpydoc packages do **not** migrate for free.
Wave 3 in §5 is where that cost lands, and it is the largest single chunk of work in this plan.

### D0 — Name and home of the artifact

The repo is `scverse-doc` with import package `scverse_doc`; the RFC calls the artifact `scverse-sphinx-theme`.

Recommendation: keep the repo as the home for everything (theme + authoring guide + registry), but publish the distribution as **`scverse-sphinx-theme`** with import package `scverse_sphinx_theme` and `html_theme = "scverse"`.
Rationale: it matches `pydata-sphinx-theme` / `sphinx-book-theme` naming, it is discoverable on PyPI by people searching for a Sphinx theme, and `scverse-doc` reads like a package that contains documentation *content*.
Renaming is free today (the repo has one commit) and expensive after the first release.

### D1 — Relationship to `scanpydoc` — **settled**

Greenfield replacement, clean room, one direction.
See §0.1 for the feature surface that has to be reimplemented and §1.1 for the rules.
No shim, no absorption, no shared code.

### D2 — Base theme — **decided: `pydata-sphinx-theme`** (RFC option B)

Build directly on `pydata-sphinx-theme`, not on `sphinx-book-theme`.

- **The GPL constraint removes the main argument for the book theme.** That argument was continuity: six packages already render as book-theme-via-scanpydoc, so staying on the book theme keeps them looking familiar. Since none of that CSS can be reused, there is nothing to stay continuous *with*. Every package is getting a new look no matter what, so the only question left is which base is better to own for the next five years.
- **Book theme is a layer we would pay for and route around.** `sphinx-book-theme` 1.1.4 sits on `pydata-sphinx-theme` 0.15.4 and lags it. Every pydata feature this RFC wants — top navbar, header dropdowns, announcement bar, version switcher — arrives through a layer whose own model (one book, one left rail) is the wrong information architecture for "one ecosystem, many packages". Two upstreams to track instead of one, and the extra one is the one that moves slower.
- **Fil's experience points the same way** — working directly against pydata was preferable. That is a real data point from someone who has maintained a scverse theme on both, and it agrees with the structural argument, so I am not treating it as merely anecdotal.
- **Easier?** Honestly: slightly *harder* in week one, clearly easier from month two. Week one is harder because the book theme ships opinionated defaults (left rail, page-level chrome, repository buttons) that we now have to compose ourselves out of pydata's `navbar_*` / `footer_*` component lists. From month two it is easier because there is one upstream to track, one set of option names, one place to look when something renders wrong, and no more "is this the book theme's opinion or ours?" when debugging CSS. The composition work is one-time and lands in M1/M4; the debugging tax would be forever.
- **Risk to accept:** pydata 0.15 → current has churn in template partial names, and we hold two overrides (§2, Layer 1). That is what the weekly upstream-drift build in §6 is for.

Cost to state honestly in the RFC: the theme option *names* differ (`repository_url` / `use_repository_button` / `path_to_docs` are book-theme options; pydata uses `use_edit_page_button` plus `html_context` GitHub keys, `icon_links`, `navbar_*`, `switcher`).
So migration is not a no-op diff for the eight book-theme packages either, which motivates D3.

### D3 — Packages must not touch base-theme options (architectural rule)

The config layer is an **abstraction boundary**, not a convenience shim.
Packages declare intent (`package=`, `repo=`, `accent=`), and the theme translates that into whatever the base theme currently wants.
If packages set `html_theme_options` keys themselves, a future base-theme bump becomes N pull requests again — which is problem #2 in the RFC, reintroduced.

Enforcement: the theme warns (and fails under `-W`) when it sees a `html_theme_options` key it owns.

### D4 — Token source of truth

Options: vendor the tokens here and sync from the website; or publish a tiny `scverse-brand` token artifact (JSON + CSS) that both the website and the theme consume.

Recommendation: start by **vendoring with a generator script and a test** (`scripts/sync_brand_tokens.py` reads `main.scss`, emits `tokens.json` + `_tokens.css`; a test fails when the two diverge), and only extract a separate artifact if the website team wants to consume it back.
Doing it by hand guarantees docs/website drift, which is the same class of bug the RFC is trying to fix.

## 2. Architecture

Three layers, as in the RFC, plus a fourth that the RFC implies but does not name.

### Layer 1 — Theme

Standard Sphinx theme registered via `[project.entry-points."sphinx.html_themes"]`, so `html_theme = "scverse"` resolves after install.
`theme.conf` inherits `pydata_sphinx_theme`.
Brand values live in `_tokens.css` as custom properties, mapped onto pydata's `--pst-*` variables in `scverse.css`; the dark palette overrides *tokens only*, never component rules.

Template overrides are a maintenance liability across pydata releases, so keep them to the minimum: an ecosystem-dropdown partial and a footer partial.
Everything else goes through `html_theme_options` component lists (`navbar_start`, `navbar_center`, `navbar_end`, `footer_start`, `footer_center`).

### Layer 2 — Config

An importable module, not magic.
Sphinx `conf.py` is exec'd as a module namespace, so the ergonomic form is a function returning a dict of config values, with every piece also individually importable for packages that need to deviate:

```python
# docs/conf.py — target end state
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

Deliberately *not* an extension that injects defaults at `config-inited`: Sphinx has already applied `conf.py` values by then, so "default here, override there" requires comparing against Sphinx defaults and misfires whenever a package legitimately sets a value equal to the default.
Use an extension only for things that must hook the build (registry-driven navbar, `switcher.json` emission, asset injection, the convention linter).

### Layer 3 — Registry

`registry.json` is a **generated artifact**, shipped as package data, built by `scripts/build_registry.py` from `scverse/ecosystem-packages` (`packages/*/meta.yaml`) and `scverse.github.io/content/packages/_index.md`, with hand-maintained overrides only for accents and inventory URLs that cannot be derived.
One dict then drives three things at once: the "scverse packages" navbar dropdown, the per-package accent, and `intersphinx_mapping`.

Two constraints worth designing for now:

- Do **not** default to intersphinx against all 80 ecosystem packages; every entry is a network fetch per build. `intersphinx()` returns a curated core set by default (python, numpy, scipy, pandas, matplotlib, anndata, mudata, scanpy, and the caller's own declared extras) with everything else opt-in by name.
- Nightly CI resolves every `objects.inv` in the registry and opens an issue on failure. That, and only that, is what makes RFC problem #3 ("links break silently") actually go away.

### Layer 4 — Conventions, with teeth

The RFC's component vocabulary, TOC order, and octicon map are conventions.
Conventions without a checker regress within two release cycles.

Ship an opt-in Sphinx extension that emits warnings (so `-W` enforces it in the packages that want enforcement) for: missing required top-level pages, top-level toctree order deviating from canonical, custom admonition titles, `html_theme_options` keys owned by the theme, and cards whose icon does not match the concept map.
Plus a reference `index` + kitchen-sink page in this repo's own docs, so "the right choice" is copy-pasteable.

### Accessibility constraint on accents (design detail that has to be settled early)

The existing per-package accents cannot be used as link colours.
`#6cf1a1` (muon) and `#fbb822` (scvi-tools) fail WCAG AA against white; several fail against a dark background.

So the token contract must be: the raw accent is for **decorative and structural** surfaces only (hero, active-nav underline, badges, card top-borders), and links/text use a *derived* pair of shades — one light-mode-safe, one dark-mode-safe — computed from the accent.
A unit test computes contrast ratios for every registry accent in both modes and fails the build if any derived shade drops below 4.5:1.
This is cheap to add now and effectively impossible to retrofit once packages have shipped accents.

## 3. Repo layout

```
scverse-doc/
├── pyproject.toml                       # dist: scverse-sphinx-theme; entry point sphinx.html_themes
├── src/scverse_sphinx_theme/
│   ├── __init__.py                      # setup_docs(), setup(), re-exports
│   ├── config.py                        # EXTENSIONS, MYST_*, NAPOLEON_*, theme_options(), intersphinx()
│   ├── registry.py                      # loads registry.json; Package dataclass; accents; inventories
│   ├── registry.json                    # GENERATED — do not hand-edit
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
├── docs/                                # dogfoods the theme; doubles as authoring guide + kitchen sink
└── tests/
    ├── roots/                           # fixture doc trees (minimal, full, deviant)
    ├── test_build.py                    # -W builds, HTML assertions
    ├── test_tokens.py                   # contrast + drift-vs-website
    └── test_registry.py                 # schema, and (nightly) inventory reachability
```

## 4. Milestones

Sized in "focused days", assuming one implementer and review latency in parallel.

### M0 — Decisions and skeleton (0.5 d + discussion latency)

D0 and D4 resolved in the RFC thread (D1 and D2 are settled above; D3 is a rule, not a question).
Repo renamed if D0 says so, dependency set trimmed (the cookiecutter scaffold currently pulls `anndata` and `session-info2`, neither of which a theme needs), theme entry point registered, `html_theme = "scverse"` resolves in a fixture build.
Exit: `sphinx-build` of `tests/roots/minimal` succeeds with the new theme and no warnings.

### M1 — Tokens and dark mode (2 d)

`sync_brand_tokens.py`, `_tokens.css`, the `--pst-*` mapping, Inter subsetting and self-hosting, the derived-accent contrast machinery, and a hand-designed dark palette (net new — nothing upstream to extract).
Exit: kitchen-sink page renders correctly in light and dark; contrast test green for every registry accent.

### M2 — Config layer (2 d)

`EXTENSIONS` and the MyST/napoleon/typehints/copybutton/opengraph defaults lifted from the cookiecutter `conf.py` and reconciled against what anndata/scanpy/pertpy actually set.
`setup_docs()`, `theme_options()`, the theme-owned-key warning.
Exit: the cookiecutter's ~40-line block reduces to the ~8-line call, byte-identical HTML for a fixture tree.

### M2.5 — Clean-room replacements for the scanpydoc extensions (3–4 d)

This milestone exists only because of the GPL constraint, and it is the difference between "eight packages can migrate" and "all fourteen can".

- `linkcode_resolve` factory driven by the existing `repo` value, RTD-aware, replacing `rtd_github_links` (anndata, scanpy, rapids_singlecell block on this).
- Type-annotation rendering: first *measure* what `sphinx-autodoc-typehints` plus `scverse_misc.sphinx_ext` already produce for anndata's and scanpy's `qualname_overrides` cases, then implement only the residue. This may turn out to be a config recipe rather than code, which would be the best outcome.
- Param-field rendering: attempt CSS-only before writing a `definition_list_typed_field` equivalent.
- Decide `autosummary_generate_imported` (reimplement in `scverse-misc`, or confirm current Sphinx covers it).

Written from rendered output and public docs, per §1.1, with provenance noted in each PR.
Exit: a fixture tree exercising all four capabilities renders correctly, and pertpy + ehrdata build with `scanpydoc` fully uninstalled.

### M3 — Registry (2 d)

`build_registry.py`, `registry.json`, `intersphinx()` with the curated-core default, the navbar ecosystem dropdown driven by the registry, nightly inventory-reachability workflow.
Exit: dropdown lists every core package plus ecosystem entries; a deliberately broken inventory URL fails the nightly job.

### M4 — Chrome (2 d)

Footer (NumFOCUS, governance, license), announcement banner wired to a single governance-controlled URL published by `scverse.github.io` (note: pydata fetches this client-side, so the endpoint needs permissive CORS), `use_edit_page_button` derived from `repo`, `switcher.py`.

On the version switcher: do **not** call the Read the Docs API during the Sphinx build — a network dependency in the docs build is a flaky-CI generator.
Instead ship a scheduled/on-release GitHub workflow (delivered via the cookiecutter) that regenerates `switcher.json` and commits it.
Exit: switcher works on an RTD preview build of this repo.

### M5 — Conventions and reference docs (2 d)

`conventions.py` warnings, the authoring guide, the reference `index` hero and API overview page, the octicon/badge maps.
Exit: `tests/roots/deviant` produces exactly the expected warning set.

### M6 — Pilots (3–4 d, mostly review latency)

See §5 for ordering.
Exit: two pilot packages merged and rendering; migration guide written from what actually broke, not from what we predicted would break.

### M7 — Cookiecutter and rollout (1 d + adoption latency)

`cookiecutter-scverse`'s `conf.py`, `pyproject.toml` doc deps, and the `switcher.json` workflow updated; `cruft` propagates to opted-in repos.
The generated `pyproject.toml` must not carry `scanpydoc` in its doc dependency group.

## 5. Rollout order (revised)

The RFC suggests piloting anndata + pertpy.
I would not start with anndata: 222-line `conf.py`, 3 local extensions, a curated `nitpick_ignore`, and the highest traffic of any scverse site.
Prove the mechanism on cheap targets first, then spend the political capital.

| Wave | Packages | Why | Rough effort each |
| --- | --- | --- | --- |
| 1 (pilot) | `annbatch`, `pertpy` | annbatch is cookiecutter-native, book theme, 4 lines of CSS — proves the "ecosystem" path. pertpy is on scanpydoc but only for `elegant_typehints`, is large, has notebook tutorials, and is maintained by the RFC author — proves the "leaving scanpydoc" path at the cheapest point on that curve. | 0.5 d / 1–2 d |
| 2 | `spatialdata`, `spatialdata-plot`, `decoupler`, `scportrait`, `pytometry`, `scvi-tools` | Book theme, ≤152 lines of CSS, no scanpydoc, mechanical. | ~0.5 d each (scvi-tools ~1 d) |
| 3 | `ehrapy`, `ehrdata`, then `anndata`, `scanpy`, `rapids_singlecell` | Leaving scanpydoc. ehrapy is theme-only so it goes first; ehrdata needs two extension replacements; anndata/scanpy/rapids_singlecell need the full M2.5 set plus their own bespoke `conf.py` logic (scanpy has 10 local extensions and a `git_ref` ordering dependency on `rtd_github_links`). Blocked on M2.5 landing. | 0.5 d / 1 d / 2–3 d each |
| 4 | `squidpy` (rtd theme), `cellrank` + `hv-anndata` (furo) | Different base theme entirely; nav structure and CSS assumptions do not carry over. | 2–3 d each |

`scripts/migrate_conf.py` should be written *during* wave 2, from wave 1's diffs — writing it before there is a real diff to generalise from is speculative.

## 6. Testing and CI

- **Build tests.** Fixture roots under `tests/roots/` built with `-W` via `sphinx.testing`: theme resolves, expected CSS/JS injected, navbar dropdown contains registry entries, `switcher.json` emitted, `intersphinx_mapping` shape, accent override applied, theme-owned-key warning fires.
- **Token tests.** Contrast ratios for all derived accents in both modes; drift check against the website's `main.scss`.
- **Registry tests.** Schema validation on every commit; `objects.inv` reachability nightly only (network).
- **Upstream-drift job.** A weekly build against `pydata-sphinx-theme` `main` — template partial renames are the main breakage risk for the two overrides we keep, and finding out from a scheduled job beats finding out from N downstream release blockers.
- **Visual regression (optional, after M5).** Playwright screenshots of the kitchen-sink page in light and dark, compared per PR. Worth it precisely because "looks consistent" is this project's actual acceptance criterion and nothing else tests it.

## 7. Risks

| Risk | Mitigation |
| --- | --- |
| GPL contamination from `scanpydoc` | §1.1 clean-room rules; never a dependency; provenance noted in PRs reimplementing a capability |
| Wave 3 stalls because scanpydoc extension replacements are missing | M2.5 delivers them *before* wave 3 starts, not during it |
| pydata option/partial churn | D3 abstraction boundary + weekly upstream-drift build + only two template overrides |
| Per-package accents fail contrast | Derived accent pair + contrast test in M1 |
| Docs/website token drift | Generator + drift test, not hand-copied hex values |
| Build slowdown from many intersphinx inventories | Curated core default, opt-in extras, `intersphinx_timeout`, cached inventories in CI |
| `nitpicky = True` plus new cross-package links surfaces a wave of warnings | Migration guide includes a `nitpick_ignore` triage step; do not ship registry-wide intersphinx and nitpicky enforcement in the same PR |
| Dark mode is net-new design with no upstream reference | Budgeted explicitly in M1; needs a design review, not just implementation |
| Adoption stalls after wave 2 | Cookiecutter default (M7) makes new packages free; conventions linter makes drift visible; waves 3–4 stay encouraged, not forced |

## 8. Suggested RFC edits

1. Add a "Prior art and why this is a clean-room rewrite" section. `scanpydoc` is GPL-3.0-or-later and this package is MPL-2.0, so it is superseded rather than extended, and none of its code, CSS, or templates can be reused. State plainly that six packages (anndata, scanpy, pertpy, ehrapy, ehrdata, rapids_singlecell) use it today, that three of them use its *extensions* and not just its theme, and that replacing those extensions is scoped work — otherwise the RFC reads as if migration is a `html_theme` one-liner for everyone.
2. Replace "final hex values TBD from the official logo" with the extracted palette from `scverse.github.io/assets/main.scss`, and note that the dark palette is the only genuinely undecided part.
3. Correct the drift inventory: four themes in use, including `sphinx_rtd_theme` (squidpy) and `furo` (cellrank, hv-anndata). These are the packages the RFC's plan is least likely to reach, and saying so up front is better than discovering it in wave 4.
4. State the registry as *derived* from `scverse/ecosystem-packages` + the website's package TOML, rather than as a new hand-maintained dict.
5. Add the "packages never set base-theme options" rule (D3) to the Approach section — it is what makes the "single upgrade point" claim true rather than aspirational.
6. Add the accent-contrast constraint to the design-tokens section, and reframe `--scverse-color-accent` as decorative-only with derived link shades.
7. Under Alternatives, note that being opinionated only holds if it is checked; reference the conventions linter as the mechanism.
