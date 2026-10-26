# SPDX-License-Identifier: MPL-2.0
"""Bundle the theme stylesheets into minified ``*.min.css``, saving browsers a request per `@import`.

Stdlib only: ``hatch_build.py`` runs this before the package is installed.
"""

from __future__ import annotations

import shutil
import subprocess
import sysconfig
from pathlib import Path

STYLES = Path(__file__).parent / "scverse" / "static" / "styles"


def find_lightningcss() -> str | None:
    """Find the binary `lightningcss-cli` installs into the env, which needn’t be on $PATH."""
    return shutil.which("lightningcss", path=sysconfig.get_path("scripts"))


def bundle(exe: str) -> None:
    """Bundle each ``styles/*.css`` into ``*.min.css`` next to it; ``_*.css`` partials are only imported.

    Wheels ship no sources, so this is a no-op outside of source trees.
    """
    for src in STYLES.glob("[!_]*.css"):
        if not src.name.endswith(".min.css"):
            # No --targets, so modern syntax like light-dark() passes through untouched.
            subprocess.run([exe, "--bundle", "--minify", src, "-o", src.with_suffix(".min.css")], check=True)
