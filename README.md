# scverse-doc

[![Tests][badge-tests]][tests]
[![Documentation][badge-docs]][documentation]

[badge-tests]: https://img.shields.io/github/actions/workflow/status/scverse/scverse-doc/test.yaml?branch=main
[badge-docs]: https://app.readthedocs.org/projects/scverse-doc/badge/

The shared Sphinx theme and documentation configuration for scverse packages.

Install it, and a package's `conf.py` becomes:

```python
extensions = ["scverse_doc"]
html_theme = "scverse"

html_theme_options = {"repo": "scverse/pertpy"}
```

That gets you the scverse brand and dark mode, the shared navbar, footer, and announcement banner, a "scverse packages" dropdown generated from the package registry, cross-links to every core package, and the standard extension stack.

## Getting started

Please refer to the [documentation][],
in particular, the [API documentation][].

## Installation

You need to have Python 3.12 or newer installed on your system.
If you don't have Python installed, we recommend installing [uv][].

We recommend managing dependencies in project-specific virtual environments to avoid dependency conflicts.
This is most convenient using package managers such as [uv][].
Choose from the options below to install scverse-doc:

<!--
1. Add the latest release of `scverse-doc` from [PyPI][] to your `uv` project:

   ```bash
   uv add scverse-doc
   ```

1. Install the latest release into a [standard virtual environment][venv]:

   ```bash
   (after activating your venv)
   pip install scverse-doc
   ```

-->

1. Install the latest development version:

   ```bash
   pip install git+https://github.com/scverse/scverse-doc.git  # (or `uv add`)
   ```

## Release notes

See the [changelog][].

## Contact

For questions and help requests, you can reach out in the [scverse discourse][].
If you found a bug, please use the [issue tracker][].

## Citation

> t.b.a

[uv]: https://github.com/astral-sh/uv
[scverse discourse]: https://discourse.scverse.org/
[issue tracker]: https://github.com/scverse/scverse-doc/issues
[tests]: https://github.com/scverse/scverse-doc/actions/workflows/test.yaml
[documentation]: https://scverse-doc.readthedocs.io
[changelog]: https://scverse-doc.readthedocs.io/page/changelog.html
[api documentation]: https://scverse-doc.readthedocs.io/page/api.html
[pypi]: https://pypi.org/project/scverse-doc
[venv]: https://docs.python.org/3/tutorial/venv.html
