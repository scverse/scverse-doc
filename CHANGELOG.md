# Changelog

## [0.6.0](https://github.com/scverse/scverse-doc/compare/v0.5.3...v0.6.0) (2026-11-24)

### Features

* edit links for generated documents ([#100](https://github.com/scverse/scverse-doc/issues/100)) ([41b5779](https://github.com/scverse/scverse-doc/commit/41b5779b5ce41438dfb54431b43b725b7df8a7aa))

## [0.5.3](https://github.com/scverse/scverse-doc/compare/v0.5.2...v0.5.3) (2026-11-24)

### Bug Fixes

* the sticky article header’s shadow appears only once the page is scrolled, by working around a [lightningcss minification bug](https://github.com/parcel-bundler/lightningcss/issues/1369) ([#98](https://github.com/scverse/scverse-doc/issues/98)) ([f9b0afe](https://github.com/scverse/scverse-doc/commit/f9b0afe68ba333b714dd6e3a58a9dad24e90d928))

## [0.5.2](https://github.com/scverse/scverse-doc/compare/v0.5.1...v0.5.2) (2026-11-24)

### Features

* the registry covers scverse’s infrastructure repositories (e.g. `scverse-doc`, `cookiecutter-scverse`) as `kind="infrastructure"` ([#96](https://github.com/scverse/scverse-doc/issues/96)) ([551ac4f](https://github.com/scverse/scverse-doc/commit/551ac4f112d31b382c953126900687d48803cbac))
* the scverse branding depends on the package’s registry entry: ecosystem packages get the scverse menu and Discourse link, scverse’s own packages also the footer’s scverse lines and the announcement banner, and unregistered projects none of it ([#96](https://github.com/scverse/scverse-doc/issues/96)) ([551ac4f](https://github.com/scverse/scverse-doc/commit/551ac4f112d31b382c953126900687d48803cbac))

## [0.5.1](https://github.com/scverse/scverse-doc/compare/v0.5.0...v0.5.1) (2026-11-05)

### Bug Fixes

* `release-notes` nests Markdown notes under its version headings again when `.md` is parsed by MyST-NB ([#87](https://github.com/scverse/scverse-doc/issues/87)) ([5ec70cc](https://github.com/scverse/scverse-doc/commit/5ec70cc01c35097854fab83420632d89f83b198a))

## [0.5.0](https://github.com/scverse/scverse-doc/compare/v0.4.0...v0.5.0) (2026-11-05)

### Features

* the site navigation shows a page’s sections that contain a toctree as captions above their entries, toggled by the `sidebar_sections_with_toctrees` theme option ([#85](https://github.com/scverse/scverse-doc/issues/85)) ([0afcc6c](https://github.com/scverse/scverse-doc/commit/0afcc6c609594acd3de57253a40469df864ebb4b))
* `[source]` links work for modules in the docs directory ([#86](https://github.com/scverse/scverse-doc/issues/86)) ([322e699](https://github.com/scverse/scverse-doc/commit/322e699a8cc17b1e2b9c05e48435ffa0c563da9c))
* `release-notes` parses each file by its suffix, so e.g. Markdown notes work on a reST page ([#86](https://github.com/scverse/scverse-doc/issues/86)) ([322e699](https://github.com/scverse/scverse-doc/commit/322e699a8cc17b1e2b9c05e48435ffa0c563da9c))

### Bug Fixes

* `release-notes` with a relative path works inside other directives, e.g. `rest-example` ([#86](https://github.com/scverse/scverse-doc/issues/86)) ([322e699](https://github.com/scverse/scverse-doc/commit/322e699a8cc17b1e2b9c05e48435ffa0c563da9c))

## [0.4.0](https://github.com/scverse/scverse-doc/compare/v0.3.0...v0.4.0) (2026-11-02)

### ⚠ BREAKING CHANGES

* Sphinx 9.1 or newer is required ([#75](https://github.com/scverse/scverse-doc/issues/75)) ([0eaabce](https://github.com/scverse/scverse-doc/commit/0eaabce254e4360927fe1a96392f6e17ec60f9ec))

### Features

* `scverse_doc.math_core` renders math to MathML at build time via [math-core](https://github.com/tmke8/math-core) instead of MathJax ([#75](https://github.com/scverse/scverse-doc/issues/75)) ([0eaabce](https://github.com/scverse/scverse-doc/commit/0eaabce254e4360927fe1a96392f6e17ec60f9ec))
  * `math_core_options` configures the converter, e.g. with macros
  * math-core’s `mathmlfixes.css` is included, fixing e.g. `\boxed` and `\cancel` in Chromium

### Bug Fixes

* rapids-singlecell’s accents are synced from the website ([#78](https://github.com/scverse/scverse-doc/issues/78)) ([ddfb6f4](https://github.com/scverse/scverse-doc/commit/ddfb6f460f5600a5c905b276e2f5fb2509196837))
* mantispy’s accents are synced from the website ([#81](https://github.com/scverse/scverse-doc/issues/81)) ([1337853](https://github.com/scverse/scverse-doc/commit/1337853f2935e458d268060a35cddeac79b95886))
* liana’s, CellRank’s and PyDESeq2’s accents and squidpy’s second accent are synced from the website ([#83](https://github.com/scverse/scverse-doc/issues/83)) ([399da7c](https://github.com/scverse/scverse-doc/commit/399da7cf04834f4238862e1aa581ddcb4320003a))

## [0.3.0](https://github.com/scverse/scverse-doc/compare/v0.2.4...v0.3.0) (2026-10-22)

### Features

* `secondary_accent` theme option for the sidebar captions, which `True` sets to the package’s second brand colour from the website ([#73](https://github.com/scverse/scverse-doc/issues/73)) ([519e3a4](https://github.com/scverse/scverse-doc/commit/519e3a42db2232e1b408c41cf6315d23e3413186))
* package accent colors are synced from the scverse website’s `accents.json` ([#74](https://github.com/scverse/scverse-doc/issues/74)) ([a999c3c](https://github.com/scverse/scverse-doc/commit/a999c3c7c3ba90ed4e7dd69db030fdfa122c3384))

### Bug Fixes

* header shadow now only extends downward ([#70](https://github.com/scverse/scverse-doc/issues/70)) ([34d4574](https://github.com/scverse/scverse-doc/commit/34d45746b3b9fdedf650c964091d3b21e148714a))
* the autosummary class template now correctly handles classes referenced through aliased modules ([#71](https://github.com/scverse/scverse-doc/issues/71)) ([1130827](https://github.com/scverse/scverse-doc/commit/11308278ecb1738800c0c22d14637772ea5cd239))
* pertpy’s accent is its logo blue instead of scirpy’s pink ([#72](https://github.com/scverse/scverse-doc/issues/72)) ([c93914a](https://github.com/scverse/scverse-doc/commit/c93914a6d9f92e0cda7e1f218fd13d0a5b6902dd))

## [0.2.3](https://github.com/scverse/scverse-doc/compare/v0.2.2...v0.2.3) (2026-10-20)

### Features

* `scverse_doc.config.DEFAULTS` is now a class ([#69](https://github.com/scverse/scverse-doc/issues/69)) ([567421f](https://github.com/scverse/scverse-doc/commit/567421ff492ea81482390f26293cefaa95cad813))

## [0.2.2](https://github.com/scverse/scverse-doc/compare/v0.2.1...v0.2.2) (2026-10-20)

### Bug Fixes

* run the private-base-skipping code on the real class names in more cases ([#66](https://github.com/scverse/scverse-doc/issues/66)) ([e053d15](https://github.com/scverse/scverse-doc/commit/e053d150b2e979ec4350597321be7c5508fc641f))
* make logo and search button fill sidebar ([#67](https://github.com/scverse/scverse-doc/issues/67)) ([c63b0ac](https://github.com/scverse/scverse-doc/commit/c63b0ac3e9fe3b6fdeebe115f7ea887ff4551583))

## [0.2.1](https://github.com/scverse/scverse-doc/compare/v0.2.0...v0.2.1) (2026-10-19)

### Bug Fixes

* Hiding private base classes no longer crashes when a base is a string or has no `__name__` ([#63](https://github.com/scverse/scverse-doc/issues/63)) ([fa00c81](https://github.com/scverse/scverse-doc/commit/fa00c81d38696d8332eb6b6e4db82f990a7c27ec))

## [0.2.0](https://github.com/scverse/scverse-doc/compare/v0.1.1...v0.2.0) (2026-10-19)

### Features

* Annotate prose return sections’ items with the members of a returned tuple ([#56](https://github.com/scverse/scverse-doc/issues/56)) ([29bcc7a](https://github.com/scverse/scverse-doc/commit/29bcc7a4e65c2a8e5ef057004e385952424d5693))
* `release-notes` directive, ported from `scanpydoc` ([#57](https://github.com/scverse/scverse-doc/issues/57)) ([da7cb25](https://github.com/scverse/scverse-doc/commit/da7cb25105eabb0c9007e53a569d778ce0202678))
* Parameters and attributes as definition lists, ported from `scanpydoc`’s `definition_list_typed_field` ([#59](https://github.com/scverse/scverse-doc/issues/59)) ([4a3b80c](https://github.com/scverse/scverse-doc/commit/4a3b80c750acf3926e416b26aa707c5a5c2ce0dd))
* `xref_overrides`, ported from `scanpydoc`’s `qualname_overrides`, also for Sphinx’ own annotations, and reporting unused entries ([#60](https://github.com/scverse/scverse-doc/issues/60)) ([25a43c6](https://github.com/scverse/scverse-doc/commit/25a43c655b5e0fb1df851d0a36f234ec78067e7e))

## [0.1.1](https://github.com/scverse/scverse-doc/compare/v0.1.0...v0.1.1) (2026-10-13)

### Bug Fixes

* Handle attributes, i.e annotated fields on classes ([#47](https://github.com/scverse/scverse-doc/issues/47)) ([01c10ae](https://github.com/scverse/scverse-doc/commit/01c10ae39c1aac487309f798fae8fffb9a4fe706))

## 0.1.0 (2026-10-13)

### Features

* `scverse` Sphinx theme: branding, dark mode, shared sidebar, footer, and announcement banner
* Package registry, fetched at runtime: “scverse packages” dropdown and intersphinx cross-links
* Source links: “edit this page” and repository icon
* Read the Docs integration: version selector and search, both with dark mode
* Autodoc, prose, and confval rendering extensions (from scverse-misc)
