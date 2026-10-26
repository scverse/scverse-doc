# SPDX-License-Identifier: MPL-2.0
"""Build the theme’s ``styles/*.min.css``, see ``scverse_doc.theme._bundle``."""

from __future__ import annotations

import runpy
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CSSBundleHook(BuildHookInterface):  # type: ignore[type-arg]
    """Bundle the theme stylesheets."""

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:  # noqa: D102
        # By path, as the package isn’t installed yet.
        mod = runpy.run_path(str(Path(self.root) / "src/scverse_doc/theme/_bundle.py"))
        if (exe := mod["find_lightningcss"]()) is None:
            msg = "lightningcss binary not found"
            raise RuntimeError(msg)
        mod["bundle"](exe)
