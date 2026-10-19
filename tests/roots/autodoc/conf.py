# SPDX-License-Identifier: MPL-2.0
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

project = "autodoc"
# No theme: the subextensions work without it.
extensions = ["scverse_doc.autodoc", "scverse_doc.napoleon"]
autosummary_generate = True
autodoc_default_options = {"show-inheritance": True}
