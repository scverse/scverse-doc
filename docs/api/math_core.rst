``scverse_doc.math_core``
=========================

.. automodule:: scverse_doc.math_core

Configuration
-------------

..  confval:: math_core_options
    :type: dict
    :default: ``{}``

    Keyword arguments for math-core’s |LatexToMathML|_, e.g. macros
    (named without the backslash, arguments as ``#1`` etc.):

    ..  code-block:: python

        math_core_options = dict(
            macros={"R": r"\mathbb{R}", "vec": r"\mathbf{#1}"},
        )

.. |LatexToMathML| replace:: ``LatexToMathML``
.. _LatexToMathML: https://github.com/tmke8/math-core/tree/main/crates/math-core-python#latextomathml
