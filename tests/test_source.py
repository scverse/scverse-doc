# SPDX-License-Identifier: MPL-2.0
"""The repository description derived from the ``source_*`` config values."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest
from sphinx.errors import ConfigError

import scverse_doc
from scverse_doc.source._forge import Provider, Source, html_context, theme_options
from scverse_doc.source._links import configure_linkcode, linkcode_url

if TYPE_CHECKING:
    from collections.abc import Mapping

    from sphinx.config import Config


def config(**overrides: str) -> Config:
    """A stand-in for the config values :func:`scverse_doc.source.setup` registers."""
    defaults = {
        "source_repository": "",
        "source_branch": "",
        "source_directory": "docs",
        "source_code_directory": "src",
        "source_provider": "",
    }
    return cast("Config", SimpleNamespace(**defaults | overrides))


@pytest.fixture(autouse=True)
def _no_rtd(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("READTHEDOCS_GIT_IDENTIFIER", "READTHEDOCS_VERSION_TYPE"):
        monkeypatch.delenv(name, raising=False)


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        pytest.param({}, "main", id="local"),
        pytest.param({"READTHEDOCS_GIT_IDENTIFIER": "1.2.x"}, "1.2.x", id="rtd-branch"),
        pytest.param({"READTHEDOCS_GIT_IDENTIFIER": "42", "READTHEDOCS_VERSION_TYPE": "external"}, "main", id="rtd-pr"),
    ],
)
def test_derives_ref(monkeypatch: pytest.MonkeyPatch, env: Mapping[str, str], expected: str) -> None:
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    source = Source.from_config(config(source_repository="https://github.com/scverse/pertpy"))
    assert source is not None
    assert source.ref == expected


def test_branch_option_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("READTHEDOCS_GIT_IDENTIFIER", "1.2.x")
    source = Source.from_config(config(source_repository="https://github.com/scverse/pertpy", source_branch="master"))
    assert source is not None
    assert source.ref == "master"


def test_no_repository() -> None:
    assert Source.from_config(config()) is None


@pytest.mark.parametrize(
    ("repository", "url", "provider"),
    [
        pytest.param(
            "https://github.com/scverse/pertpy/", "https://github.com/scverse/pertpy", Provider.github, id="github"
        ),
        pytest.param("https://gitlab.com/o/r", "https://gitlab.com/o/r", Provider.gitlab, id="gitlab"),
        # A self-hosted instance is recognised by its host name.
        pytest.param(
            "https://gitlab.example.org/o/r", "https://gitlab.example.org/o/r", Provider.gitlab, id="self-hosted"
        ),
        pytest.param("https://git.example.org/o/r", "https://git.example.org/o/r", Provider._unknown, id="unknown"),
    ],
)
def test_derives_url_and_provider(repository: str, url: str, provider: Provider) -> None:
    source = Source.from_config(config(source_repository=repository))
    assert source is not None
    assert (source.url, source.provider) == (url, provider)


def test_provider_can_be_declared() -> None:
    source = Source.from_config(config(source_repository="https://git.example.org/o/r", source_provider="github"))
    assert source is not None
    assert source.provider is Provider.github


@pytest.mark.parametrize("name", [pytest.param("Github", id="typo"), pytest.param("_unknown", id="placeholder")])
def test_unusable_provider_says_what_it_knows(name: str) -> None:
    with pytest.raises(ConfigError, match=r"'github', 'gitlab', 'bitbucket'"):
        Source.from_config(config(source_repository="https://git.example.org/o/r", source_provider=name))


GITHUB = Source(
    url="https://github.com/scverse/pertpy", ref="main", directory="docs", code="src", provider=Provider.github
)
UNKNOWN = Source(
    url="https://git.example.org/o/r", ref="main", directory="docs", code="src", provider=Provider._unknown
)


def test_view_links_at_lines() -> None:
    assert GITHUB.view("docs/index.md") == "https://github.com/scverse/pertpy/blob/main/docs/index.md"
    assert GITHUB.view("a.py", (3, 7)) == "https://github.com/scverse/pertpy/blob/main/a.py#L3-L7"


def test_unknown_forge_links_only_to_the_repository() -> None:
    assert UNKNOWN.view("docs/index.md") is None
    assert UNKNOWN.icon_link["url"] == "https://git.example.org/o/r"
    assert "use_edit_page_button" not in theme_options(UNKNOWN)


def test_theme_options_cover_the_themes_we_know() -> None:
    options = theme_options(GITHUB)
    # sphinx-book-theme’s header buttons
    assert options["use_repository_button"] is True
    assert options["use_source_button"] is True
    assert options["use_issues_button"] is True
    # furo / sphinx-basic-ng
    assert options["source_repository"] == "https://github.com/scverse/pertpy"
    assert (options["source_branch"], options["source_directory"]) == ("main", "docs")
    # sphinx-book-theme
    assert options["repository_url"] == "https://github.com/scverse/pertpy"
    assert (options["repository_branch"], options["path_to_docs"]) == ("main", "docs")
    assert options["repository_provider"] == "github"
    # pydata-sphinx-theme
    assert options["use_edit_page_button"] is True


def test_html_context_is_what_the_themes_build_edit_urls_from() -> None:
    assert html_context(GITHUB) == {
        "display_github": True,
        "github_url": "https://github.com",
        "github_host": "github.com",
        "github_user": "scverse",
        "github_repo": "pertpy",
        "github_version": "main",
        "doc_path": "docs",
        "conf_py_path": "/docs/",
    }


def test_html_context_names_the_declared_forge() -> None:
    """A self-hosted instance keeps its host, but the entries are the forge’s."""
    gitlab = Source.from_config(config(source_repository="https://gitlab.example.org/group/sub/r"))
    assert gitlab is not None
    assert html_context(gitlab) == {
        "display_gitlab": True,
        "gitlab_url": "https://gitlab.example.org",
        "gitlab_host": "gitlab.example.org",
        "gitlab_user": "group/sub",
        "gitlab_repo": "r",
        "gitlab_version": "main",
        "doc_path": "docs",
        "conf_py_path": "/docs/",
    }


@pytest.mark.parametrize(
    ("module", "fullname", "path"),
    [
        pytest.param("scverse_doc.registry", "intersphinx", "src/scverse_doc/registry.py", id="module"),
        # A package resolves to its ``__init__.py``, one level deeper than its name.
        pytest.param("scverse_doc.theme", "setup", "src/scverse_doc/theme/__init__.py", id="package"),
        pytest.param("scverse_doc.source._forge", "Source.view", "src/scverse_doc/source/_forge.py", id="private"),
    ],
)
def test_linkcode_finds_our_own_source(module: str, fullname: str, path: str) -> None:
    url = linkcode_url(GITHUB, module, fullname)
    assert url is not None
    prefix, _, lines = url.partition("#")
    assert prefix == f"https://github.com/scverse/pertpy/blob/main/{path}"
    assert lines.startswith("L")


def test_linkcode_finds_docs_source() -> None:
    srcdir = Path(scverse_doc.__file__).parent.parent  # pretend `src/` holds the docs
    url = linkcode_url(GITHUB, "scverse_doc.registry", "intersphinx", srcdir)
    assert url is not None
    assert url.startswith(f"https://github.com/scverse/pertpy/blob/main/{GITHUB.directory}/scverse_doc/registry.py#L")


@pytest.mark.parametrize(
    ("module", "fullname"),
    [
        pytest.param("scverse_doc.registry", "nope", id="unlocatable"),
        pytest.param("scverse_doc.source._forge", "ConfigError", id="other-package"),
    ],
)
def test_linkcode_gives_up_quietly(module: str, fullname: str) -> None:
    assert linkcode_url(GITHUB, module, fullname) is None


def test_linkcode_needs_a_repository() -> None:
    app = SimpleNamespace(config=config(), extensions={"sphinx.ext.linkcode"})
    app.config.linkcode_resolve = None
    configure_linkcode(app)  # type: ignore[arg-type]
    assert app.config.linkcode_resolve is None


def test_linkcode_only_resolves_python() -> None:
    app = SimpleNamespace(
        config=config(source_repository="https://github.com/scverse/pertpy"), extensions={"sphinx.ext.linkcode"}
    )
    app.config.linkcode_resolve = None
    configure_linkcode(app)  # type: ignore[arg-type]
    assert app.config.linkcode_resolve("js", {"module": "", "fullname": "x"}) is None
