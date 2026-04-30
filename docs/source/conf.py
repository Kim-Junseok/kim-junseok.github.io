# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Junseok Kim'
copyright = '2026, Junseok Kim'
author = 'Junseok Kim'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

#html_theme = 'alabaster'

html_theme = "pydata_sphinx_theme"

html_theme_options = {
    "github_url": "https://github.com/Kim-Junseok",
    "linkedin_url": "https://www.linkedin.com/in/junsk",
    "header_links_before_dropdown": 4,
    "navbar_end": ["navbar-icon-links"],
    "footer_start": ["copyright"],
    "footer_end": [],
    "show_prev_next": False,
}

html_title = "Junseok Kim"
html_static_path = ['_static']
