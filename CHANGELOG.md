# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog][],
and this project adheres to [Semantic Versioning][].

[keep a changelog]: https://keepachangelog.com/
[semantic versioning]: https://semver.org/

## [Unreleased]

## [0.3.0]

### Added

- `secondary_accent` theme option for the sidebar captions, which `True` sets to the package’s second brand colour from the website (#73)

### Changed

- package accent colors are synced from the scverse website’s `accents.json` (#74)

### Fixed

- header shadow now only extends downward (#70)
- the autosummary class template now correctly handles classes referenced through aliased modules (#71)
- pertpy’s accent is its logo blue instead of scirpy’s pink (#72)

## [0.2.3]

### Added

- `scverse_doc.config.DEFAULTS` is now a class (#69)

## [0.2.2]

### Fixed

- run the private-base-skipping code on the real class names in more cases (#66)
- make logo and search button fill sidebar (#67)

## [0.2.1]

### Fixed

- Hiding private base classes no longer crashes when a base is a string or has no `__name__` (#63)

## [0.2.0]

### Added

- Annotate prose return sections’ items with the members of a returned tuple (#56)
- `release-notes` directive, ported from `scanpydoc` (#51)
- Parameters and attributes as definition lists, ported from `scanpydoc`’s `definition_list_typed_field` (#54)
- `xref_overrides`, ported from `scanpydoc`’s `qualname_overrides`, also for Sphinx’ own annotations, and reporting unused entries (#53)

## [0.1.1]

### Fixed

- Handle attributes, i.e annotated fields on classes (#47)

## [0.1.0]

### Added

- `scverse` Sphinx theme: branding, dark mode, shared sidebar, footer, and announcement banner
- Package registry, fetched at runtime: “scverse packages” dropdown and intersphinx cross-links
- Source links: “edit this page” and repository icon
- Read the Docs integration: version selector and search, both with dark mode
- Autodoc, prose, and confval rendering extensions (from scverse-misc)

[Unreleased]: https://github.com/scverse/scverse-doc/compare/v0.3.0...main
[0.3.0]: https://github.com/scverse/scverse-doc/releases/tag/v0.3.0
[0.2.3]: https://github.com/scverse/scverse-doc/releases/tag/v0.2.3
[0.2.2]: https://github.com/scverse/scverse-doc/releases/tag/v0.2.2
[0.2.1]: https://github.com/scverse/scverse-doc/releases/tag/v0.2.1
[0.2.0]: https://github.com/scverse/scverse-doc/releases/tag/v0.2.0
[0.1.1]: https://github.com/scverse/scverse-doc/releases/tag/v0.1.1
[0.1.0]: https://github.com/scverse/scverse-doc/releases/tag/v0.1.0
