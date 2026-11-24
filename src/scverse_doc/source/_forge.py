# SPDX-License-Identifier: MPL-2.0
"""The source repository as configured, and the theme options and context that point at it."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, NamedTuple, Self
from urllib.parse import urlsplit

from sphinx.errors import ConfigError

if TYPE_CHECKING:
    from pathlib import PurePosixPath

    from sphinx.application import Sphinx
    from sphinx.config import Config

__all__ = ["Provider", "Source", "configure_theme", "html_context", "theme_options"]


class _ProviderData(NamedTuple):
    """How one forge lays out its URLs, relative to the repository URL."""

    label: str
    """What a reader sees, e.g. on the icon link."""

    icon: str
    view: str
    lines: str


#: The forge layouts we can build links for, keyed by the name that appears in their hosts.
#: A self-hosted instance picks one with :confval:`source_provider`.
class Provider(_ProviderData, Enum):
    github = ("GitHub", "fa-brands fa-github", "blob/{ref}/{path}", "#L{start}-L{end}")
    gitlab = ("GitLab", "fa-brands fa-gitlab", "-/blob/{ref}/{path}", "#L{start}-{end}")
    bitbucket = ("Bitbucket", "fa-brands fa-bitbucket", "src/{ref}/{path}", "#lines-{start}:{end}")
    _unknown = ("Source", "fa-solid fa-code-branch", "", "")

    def __bool__(self) -> bool:
        return self is not self._unknown

    @classmethod
    def parse(cls, name: str, host: str) -> Provider:
        """The forge named by :confval:`source_provider`, else the one `host` is named after."""
        if not name:
            return next((member for member in cls if member and member.name in host), cls._unknown)
        if (member := cls.__members__.get(name)) is None or not member:
            known = ", ".join(repr(member.name) for member in cls if member)
            msg = f"source_provider is {name!r}, but the layouts we know are {known}."
            raise ConfigError(msg)
        return member


@dataclass(frozen=True)
class Source:
    """Where a package’s source lives, as derived from the ``source_*`` config values."""

    url: str
    """The repository URL, without a trailing slash."""

    ref: str
    """The branch or tag the links point at."""

    directory: str
    """Where the documentation sources live in the repository."""

    code: str
    """Where the importable code lives in the repository – ``"src"`` in a src layout."""

    provider: Provider
    """How this repository’s forge lays out its URLs."""

    @classmethod
    def from_config(cls, config: Config) -> Self | None:
        """Describe the repository, or :data:`None` if `conf.py` declared none."""
        if not (url := str(config.source_repository).rstrip("/")):
            return None
        host = urlsplit(url).netloc
        return cls(
            url=url,
            ref=_ref(config),
            directory=str(config.source_directory).strip("/"),
            code=str(config.source_code_directory).strip("/"),
            provider=Provider.parse(config.source_provider, host),
        )

    @property
    def icon_link(self) -> dict[str, str]:
        """The icon link pointing at the repository."""
        return {"name": self.provider.label, "url": self.url, "icon": self.provider.icon}

    def view(self, path: PurePosixPath | str, lines: tuple[int, int] | None = None) -> str | None:
        """Link to a file in the repository, optionally highlighting a line range.

        :data:`None` if the forge is unknown.
        """
        if not self.provider.view:
            return None
        fragment = self.provider.lines.format(start=lines[0], end=lines[1]) if lines else ""
        return f"{self.url}/{self.provider.view.format(ref=self.ref, path=path)}{fragment}"


def _ref(config: Config) -> str:
    """The ref links point at: the config value, else what Read the Docs is building, else ``main``."""
    if branch := config.source_branch:
        return str(branch)
    # On pull request builds the identifier is the PR number, not a ref.
    if os.environ.get("READTHEDOCS_VERSION_TYPE") != "external" and (
        ref := os.environ.get("READTHEDOCS_GIT_IDENTIFIER")
    ):
        return ref
    return "main"


def theme_options(source: Source) -> dict[str, object]:
    """Every theme option some theme reads this from; only the declared ones are applied."""
    if not source.provider:
        # Every one of these makes a theme build per-page URLs we have no layout for:
        # `sphinx-basic-ng` warns, `sphinx-book-theme` guesses the forge and errors out if it can’t.
        return {}
    options: dict[str, object] = {
        # sphinx-basic-ng, and so furo
        "source_repository": source.url,
        "source_branch": source.ref,
        "source_directory": source.directory,
        # sphinx-book-theme
        "repository_url": source.url,
        "repository_branch": source.ref,
        "repository_provider": source.provider.name,
        "path_to_docs": source.directory,
        # pydata-sphinx-theme
        "use_edit_page_button": True,
        # sphinx-book-theme’s article header buttons
        "use_repository_button": True,
        "use_source_button": True,
    }
    if source.provider in {Provider.github, Provider.gitlab}:  # sphinx-book-theme warns for the others
        options["use_issues_button"] = True
    return options


def html_context(source: Source) -> dict[str, object]:
    """The `html_context` entries `pydata-sphinx-theme`, `sphinx_rtd_theme` and `furo` read."""
    parts = urlsplit(source.url)
    owner, _, name = parts.path.strip("/").rpartition("/")
    return {
        # `sphinx_rtd_theme` picks the forge by this, `furo` gates its footer icon on it.
        f"display_{source.provider.name}": True,
        f"{source.provider.name}_url": f"{parts.scheme}://{parts.netloc}",
        f"{source.provider.name}_host": parts.netloc,
        f"{source.provider.name}_user": owner,
        f"{source.provider.name}_repo": name,
        f"{source.provider.name}_version": source.ref,
        "doc_path": source.directory,
        # What `sphinx_rtd_theme` and `furo` append straight after the ref, slashes included.
        "conf_py_path": f"/{source.directory}/" if source.directory else "/",
    }


def configure_theme(app: Sphinx) -> None:
    """Fill in whatever the selected theme understands.

    On ``builder-inited``, since which options a theme declares is only known
    once the builder created it, and writing an undeclared one warns.
    `pydata-sphinx-theme` reads these from the same event, but connects later.
    """
    config = app.config
    if (source := Source.from_config(config)) is None or (theme := getattr(app.builder, "theme", None)) is None:
        return
    declared = theme.get_options()
    options = config.html_theme_options
    for name, value in theme_options(source).items():
        if name in declared:
            options.setdefault(name, value)
    if "icon_links" in declared:
        # Prepended, so this works whichever order the theme’s own hook runs in.
        options["icon_links"] = [source.icon_link, *options.get("icon_links", [])]
    if source.provider:
        config.html_context = html_context(source) | config.html_context
