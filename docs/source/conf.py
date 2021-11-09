# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

import os
import sys

# Adds system path two folders back (where project lives.)
sys.path.insert(0, os.path.abspath("../.."))

# PyLint might complain, but the interpreter should be able to find this on run.
from httpq import *

# -- Project information -----------------------------------------------------

project = "🏃‍♂️ httpq"
copyright = "2021, Felipe Faria"
author = "Felipe Faria"

# -- General configuration ---------------------------------------------------

# Project Name
html_title = "{}".format(project)

# Order of docs.
autodoc_member_order = "bysource"

# Turn off typehints.
autodoc_typehints = "none"

# Remove module names from class docs.
add_module_names = False

# Show only class docs.
autoclass_content = "class"

# List __init___ docstrings separately from the class docstring
napoleon_include_init_with_doc = True

# Removes the default values from the documentation.
keep_default_values = False

# Removes the class values; e.g. 'Class(val, val, val):' becomes 'Class:'.
hide_class_values = True

# Automatically assume :py:obj: for '``' types.
default_role = "py:obj"

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "sphinx.ext.autodoc",
    "sphinx_copybutton",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

# Theme settings.
html_theme = "furo"
html_theme_options = {}
html_static_path = ["_static"]
