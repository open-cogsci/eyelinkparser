"""Sphinx configuration."""
project = "Python Eyelink Parser"
author = "Maciej Skorski"
copyright = "2022, Maciej Skorski"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
