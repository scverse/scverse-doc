# SPDX-License-Identifier: MPL-2.0
r"""Math rendering via ``math-core``.

Browsers support MathML today,
so math-core_ is the most lightweight way to render math on the web.

Examples
--------
Inline math, and a block equation referenced via its ``:label:``:

..  rest-example::

    :math:`e^{i\pi} = -1`, see :eq:`math-example`.

    ..  math::
        :label: math-example

        \operatorname{AA}(c_\text{fg}, c_\text{bg}) \geq 4.5

Equations separated by blank lines, or rows separated by ``\\``, are aligned at ``&``:

..  rest-example::

    ..  math::

        a &= b + c

        d &= e

``:no-wrap:`` passes the LaTeX as is, e.g. for your own environment:

..  rest-example::

    ..  math::
        :no-wrap:

        \begin{cases} 1 & x > 0 \\ 0 & \text{otherwise} \end{cases}

Configure the converter, e.g. with your own macros, via :confval:`math_core_options`.
math-core’s ``mathmlfixes.css`` is included, mainly to fix Chromium’s rendering.

.. _math-core: https://github.com/tmke8/math-core
"""

from pathlib import Path

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.locale import _
from sphinx.util import logging
from sphinx.util.math import get_node_equation_number
from sphinx.util.typing import ExtensionMetadata
from sphinx.writers.html5 import HTML5Translator

logger = logging.getLogger(__name__)


class _MathVisitor:
    def configure(self, app: Sphinx, config: Config) -> None:
        """Create the converters from :confval:`math_core_options`."""
        from math_core import LatexToMathML

        self.converter = LatexToMathML(**config.math_core_options)
        self.fallback = LatexToMathML(**{**config.math_core_options, "continue_on_error": True})

    def visit(self, renderer: HTML5Translator, node: nodes.math | nodes.math_block):
        """Handles inline math `` :math:`…` `` and block math ``.. math:: …``."""
        from math_core import LatexError

        tex = node.astext()
        if display_style := isinstance(node, nodes.math_block):
            # `starttag` sets expected `id` for `:eq:` references; markup mirrors `sphinx.ext.mathjax`
            renderer.body.append(renderer.starttag(node, "div", CLASS="math"))
            if node["number"]:
                renderer.body.append(f'<span class="eqno">({get_node_equation_number(renderer, node)})')
                renderer.add_permalink_ref(node, _("Link to this equation"))
                renderer.body.append("</span>")
            if not node.get("no-wrap", node.get("nowrap", False)):
                tex = _wrap(tex)
        try:
            out = self.converter.convert_all([(tex, display_style)])
        except LatexError as e:
            logger.warning("LaTeX error:%s", e, location=node)
            out = self.fallback.convert_all([(tex, display_style)])
        renderer.body.extend(out)
        if display_style:
            renderer.body.append("</div>\n")
        raise nodes.SkipNode


def _wrap(tex: str) -> str:
    """Align multiple equations or rows, like `sphinx.ext.mathjax`."""
    # uses ``aligned``, as math-core lacks ``split``:
    # https://github.com/tmke8/math-core/issues/154
    # TODO: once split exists, we should use Sphinx’ `wrap_displaymath` instead of this
    parts = [part.strip() for part in tex.split("\n\n") if part.strip()]
    if len(parts) == 1 and r"\\" not in parts[0]:
        return parts[0]
    return r"\begin{aligned}" + r"\\".join(parts) + r"\end{aligned}"


# `mathmlfixes.css` is synced from math-core by `scripts/sync_upstream.py`
_STATIC = Path(__file__).with_name("static")


def setup(app: Sphinx):
    """Register the custom math-core HTML renderer."""
    visitor = _MathVisitor()
    # we raise SkipNode, so no need for depart (the `None`s)
    app.add_html_math_renderer("mathcore", (visitor.visit, None), (visitor.visit, None))
    app.add_config_value("math_core_options", {}, "env", types=frozenset({dict}))
    app.connect("config-inited", visitor.configure)
    app.add_static_dir(_STATIC)
    app.add_css_file("mathmlfixes.css")
    app.add_css_file("math_core.css")
    return ExtensionMetadata(parallel_read_safe=True)
