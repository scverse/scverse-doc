# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog][],
and this project adheres to [Semantic Versioning][].

[keep a changelog]: https://keepachangelog.com/
[semantic versioning]: https://semver.org/


## [Unreleased]

### Added

- Annotate prose return sections’ items with the members of a returned tuple
- `release-notes` directive, ported from `scanpydoc` (#51)
- Parameters and attributes as definition lists, ported from `scanpydoc`’s `definition_list_typed_field` (#54)

## [0.1.1]

### Fixed

- Handle attributes (annotated fields on classes)

## [0.1.0]

### Added

- `scverse` Sphinx theme: branding, dark mode, shared sidebar, footer, and announcement banner
- Package registry, fetched at runtime: “scverse packages” dropdown and intersphinx cross-links
- Source links: “edit this page” and repository icon
- Read the Docs integration: version selector and search, both with dark mode
- Autodoc, prose, and confval rendering extensions (from scverse-misc)

[0.1.1]: https://github.com/scverse/scverse-doc/releases/tag/v0.1.1
[0.1.0]: https://github.com/scverse/scverse-doc/releases/tag/v0.1.0
