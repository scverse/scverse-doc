from scverse_doc import setup_docs

globals().update(
    setup_docs(
        package="scverse-doc",
        distribution="scverse-doc",
        repo="scverse/scverse-doc",
        announcement=None,
        exclude_patterns=["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"],
    )
)

bibtex_bibfiles = ["references.bib"]
extensions = [*extensions, "sphinxcontrib.bibtex"]  # noqa: F821
