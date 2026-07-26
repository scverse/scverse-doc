"""The scverse Sphinx theme and shared documentation configuration.

A package's `conf.py` should be a handful of assignments:

.. code:: python

   from scverse_doc import setup_docs

   globals().update(setup_docs(package="pertpy", repo="scverse/pertpy"))

Everything else — the extension stack, the brand, the navigation conventions, the cross-package links — comes from
here, so it can be changed for the whole ecosystem in one release instead of in one pull request per repository.
"""

from __future__ import annotations

import warnings
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, metadata, version
from typing import TYPE_CHECKING, Any

from . import config, registry
from ._ext import setup
from .config import OWNED_THEME_OPTIONS, theme_options
from .registry import intersphinx

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["OWNED_THEME_OPTIONS", "config", "intersphinx", "registry", "setup", "setup_docs", "theme_options"]

try:
    __version__ = version("scverse-doc")
except PackageNotFoundError:  # pragma: no cover — only when running from a source tree without an install
    __version__ = "0.0.0"


def _project_metadata(distribution: str) -> dict[str, str]:
    """Read project metadata from the installed distribution, tolerating it not being installed."""
    try:
        info = metadata(distribution)
    except PackageNotFoundError:
        return {}
    return {
        "project": info["Name"],
        "author": info["Author"] or info["Author-email"] or "",
        "version": info["Version"],
        "release": info["Version"],
    }


def setup_docs(
    *,
    package: str | None = None,
    repo: str | None = None,
    distribution: str | None = None,
    accent: str | None = None,
    intersphinx_extra: Sequence[str] = (),
    doc_path: str = "docs/",
    branch: str = "main",
    announcement: str | None = config.ANNOUNCEMENT_URL,
    theme_options_extra: dict[str, Any] | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    """Build a complete scverse `conf.py` namespace.

    Parameters
    ----------
    package
        The package's name in the scverse registry, e.g. ``"pertpy"``.
        Supplies the accent colour and marks the current package in the ecosystem dropdown.
    repo
        The GitHub repository as ``"owner/name"``.
        Drives the source link, the "edit this page" button, and the GitHub icon.
    distribution
        The installed distribution to read project metadata from, defaulting to `package`.
    accent
        Overrides the accent from the registry.
    intersphinx_extra
        Registry package names to cross-link in addition to the default core set.
    doc_path
        Path of the documentation directory within the repository, used by the "edit this page" button.
    branch
        Branch the "edit this page" button points at.
    announcement
        URL of the shared announcement fragment, or :data:`None` to opt out.
    theme_options_extra
        Extra `html_theme_options` entries.
        Keys in `scverse_doc.config.OWNED_THEME_OPTIONS` warn, because setting them here opts the package out of
        future improvements to them.
    overrides
        Any other Sphinx config value, applied last.

    Returns
    -------
    A mapping of Sphinx configuration values.
    Assign it with ``globals().update(setup_docs(...))``.

    Examples
    --------
    >>> conf = setup_docs(package="anndata", repo="scverse/anndata")
    >>> conf["html_theme"]
    'scverse'
    """
    values: dict[str, Any] = config.defaults()
    values.update(_project_metadata(distribution or package or ""))

    if author := values.get("author"):
        values["copyright"] = f"{datetime.now(tz=UTC):%Y}, {author}"

    options = theme_options(repo=repo, package=package, accent=accent, announcement=announcement)
    if theme_options_extra:
        if owned := OWNED_THEME_OPTIONS & theme_options_extra.keys():
            warnings.warn(
                f"theme_options_extra overrides options owned by the scverse theme: {', '.join(sorted(owned))}. "
                "These stop tracking ecosystem-wide changes; consider upstreaming the change instead.",
                UserWarning,
                stacklevel=2,
            )
        options.update(theme_options_extra)

    values |= {
        "html_theme": "scverse",
        "html_theme_options": options,
        "html_title": values.get("project", package or ""),
        "intersphinx_mapping": intersphinx(*intersphinx_extra),
    }

    if repo:
        owner, name = repo.split("/", 1)
        values["html_context"] = {
            "github_user": owner,
            "github_repo": name,
            "github_version": branch,
            "doc_path": doc_path,
            "default_mode": "auto",
        }

    values.update(overrides)
    return values
