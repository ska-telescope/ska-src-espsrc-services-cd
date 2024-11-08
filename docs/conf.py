# docs/source/conf.py

import os
import sys
sys.path.insert(0, os.path.abspath('../../'))

# -- Project information -----------------------------------------------------

project = 'espSRC'
author = 'The espSRC Team - Instituto de Astrofísica de Andalucía.<BR>Consejo Superior de Investigaciones Científicas - Spain'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon'
]

html_theme_options = {
    'search_bar_position': 'sidebar',  # Esto coloca la caja de búsqueda en la barra lateral
}

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_book_theme'
html_logo = '_static/logo.png'

html_static_path = ['_static']
