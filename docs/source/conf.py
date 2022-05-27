# Configuration file for the Sphinx documentation builder.

import os
import sys

# -- Project information

project = 'dcm2reg'
copyright = '2022, Andreas Busch, Philip Leth and Jonathan Nielsen'
author = 'Andreas Busch, Philip Leth and Jonathan Nielsen'

release = '0.1'
version = '0.1.0'

# -- General configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'

# -- Options for EPUB output
epub_show_urls = 'footnote'

# -- Adding folder structure to sys.path, so that Sphinx can find the .py-files
for x in os.walk('../..'):
  sys.path.insert(0, x[0])

sys.path.append(os.path.abspath('../..'))

# These folders are copied to the documentation's HTML output
html_static_path = ['_static']

# These paths are either relative to html_static_path
# or fully qualified paths (eg. https://...)
html_css_files = [
    'css/custom.css',
]

# Add JavaScript
html_js_files = [
    'js/custom.js',
]

def setup(app):
    app.add_css_file("css/custom.css")