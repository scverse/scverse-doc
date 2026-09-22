project = "pertpy"
# ``scverse_doc`` is not listed: Sphinx must load the theme from its entry point,
# and the theme must bring ``scverse_doc.source`` with it – late enough that
# ``config-inited`` has already fired.
html_theme = "scverse"
extensions = ["sphinx.ext.linkcode"]
source_repository = "https://github.com/scverse/pertpy"
source_branch = "main"
html_theme_options = {"announcement": ""}
