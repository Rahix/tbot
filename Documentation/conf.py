import os
import re
import subprocess
import sys
import typing

from docutils import nodes
from docutils.parsers import rst
import recommonmark.parser
import sphinx.util.logging
from sphinx.util.docfields import TypedField
from sphinx import addnodes

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath("./"))

# Also add the repository root so the tbot module can be found
sys.path.insert(0, os.path.abspath("../"))

logger = sphinx.util.logging.getLogger("tbot/conf.py")

# -- Project information -----------------------------------------------------
project = "tbot"
copyright = "2019, Rahix"
author = "Rahix"

# The full version, including alpha/beta/rc tags
release = (
    subprocess.run(["git", "describe", "--long"], stdout=subprocess.PIPE, check=True)
    .stdout.decode()
    .strip()[1:]
)
version = release

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "recommonmark",
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
]

source_parsers = {".md": recommonmark.parser.CommonMarkParser}
source_suffix = [".rst", ".md"]

templates_path = ["sphinx-templates"]

todo_include_todos = True

language = "en"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["output", "Thumbs.db", ".DS_Store"]

# The name of the Pygments (syntax highlighting) style to use.
if globals()["tags"].has("pygments-light"):
    pygments_style = "default"
else:
    pygments_style = "monokai"

# Intersphinx Config
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "paramiko": ("http://docs.paramiko.org/en/2.4", None),
}

# -- Options for HTML output ------------------------------------------------- {{{
# The Read the Docs theme is available from
# - https://github.com/snide/sphinx_rtd_theme
# - https://pypi.python.org/pypi/sphinx_rtd_theme
# - python-sphinx-rtd-theme package (on Debian)
try:
    import sphinx_rtd_theme

    html_theme = "sphinx_rtd_theme"
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
except ImportError:
    logger.warning(
        'The Sphinx "sphinx_rtd_theme" HTML theme was not found. Make sure you have the theme installed to produce pretty HTML output. Falling back to the default theme.'
    )

html_logo = "static/tbot-logo-white.png"
html_theme_options = {"logo_only": True, "style_external_links": True}
html_static_path = ["static"]
# }}}

# -- Options for LaTeX output ------------------------------------------------ {{{
latex_logo = "static/tbot-logo.png"
latex_elements = {
    "papersize": "a4paper",
    "preamble": r"""
\usepackage{alltt}

% This character is sometimes used in the docs
\DeclareUnicodeCharacter{1F8A5}{$\Rightarrow$}

% Because we have multiple toctrees, we need to overwrite the title
\addto\captionsenglish{\renewcommand{\contentsname}{Table Of Contents}}
""",
    "extraclassoptions": "oneside",
    "babel": r"\usepackage[english]{babel}",
}
latex_show_pagerefs = True

latex_documents = [("index", "tbot.tex", "tbot Documentation", "Rahix", "manual", True)]

# }}}

# -- Options for Autodoc ----------------------------------------------------- {{{
autoclass_content = "both"
autodoc_default_options = {"show-inheritance": None, "member-order": "bysource"}
# }}}

# -- Extension: html-console ------------------------------------------------- {{{


class HtmlConsoleDirective(rst.Directive):
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    option_spec: typing.Dict = {}

    pat_pre = re.compile(r"</?pre>")
    pat_color = re.compile(r'<font color="#([A-Z0-9]+)">(.+?)</font>')
    pat_bold = re.compile(r"<b>(.+?)</b>")

    def run(self) -> typing.List[nodes.Node]:
        self.assert_has_content()
        text = "\n".join(self.content)

        gen = []
        # Add html version
        html_text = '<div class="highlight">\n' + text + "\n</div>"
        gen.append(nodes.raw(text, html_text, format="html"))

        # Add latex version
        latex_text = "\\begin{sphinxVerbatim}[commandchars=\\\\\\{\\}]\n"
        transformed = text
        transformed = transformed.replace("\\", "\\textbackslash{}")
        transformed = self.pat_pre.sub("", transformed)
        transformed = self.pat_color.sub(r"\\textcolor[HTML]{\1}{\2}", transformed)
        transformed = self.pat_bold.sub(r"\\textbf{\1}", transformed)
        transformed = transformed.replace("&lt;", "<")
        transformed = transformed.replace("&gt;", ">")
        transformed = transformed.replace("&apos;", r"\textsc{\char39}")
        transformed = transformed.replace("&quot;", '"')
        latex_text += transformed
        latex_text += "\n\\end{sphinxVerbatim}"
        gen.append(nodes.raw(text, latex_text, format="latex"))

        return gen


# }}}


# -- Fix instance variables being cross-referenced --------------------------- {{{
def patched_make_field(
    self,  # type: TypedField
    types,  # type: typing.Dict[str, typing.List[nodes.Node]]
    domain,  # type: str
    items,  # type: typing.Tuple
    env=None,  # type: typing.Any
):
    # type: (...) -> nodes.field
    def handle_item(fieldarg, content):
        # type: (str, str) -> nodes.paragraph
        par = nodes.paragraph()
        par += addnodes.literal_strong("", fieldarg)  # Patch: this line added
        # par.extend(self.make_xrefs(self.rolename, domain, fieldarg,
        #                            addnodes.literal_strong, env=env))
        if fieldarg in types:
            par += nodes.Text(" (")
            # NOTE: using .pop() here to prevent a single type node to be
            # inserted twice into the doctree, which leads to
            # inconsistencies later when references are resolved
            fieldtype = types.pop(fieldarg)
            if len(fieldtype) == 1 and isinstance(fieldtype[0], nodes.Text):
                typename = "".join(n.astext() for n in fieldtype)
                par.extend(
                    self.make_xrefs(
                        self.typerolename,
                        domain,
                        typename,
                        addnodes.literal_emphasis,
                        env=env,
                    )
                )
            else:
                par += fieldtype
            par += nodes.Text(")")
        par += nodes.Text(" -- ")
        par += content
        return par

    fieldname = nodes.field_name("", self.label)
    if len(items) == 1 and self.can_collapse:
        fieldarg, content = items[0]
        bodynode = handle_item(fieldarg, content)
    else:
        bodynode = self.list_type()
        for fieldarg, content in items:
            bodynode += nodes.list_item("", handle_item(fieldarg, content))
    fieldbody = nodes.field_body("", bodynode)
    return nodes.field("", fieldname, fieldbody)


if sphinx.version_info < (4, 0, 0):
    TypedField.make_field = patched_make_field
# }}}


# -- Sphinx Setup ------------------------------------------------------------
def setup(app: typing.Any) -> None:
    app.add_directive("html-console", HtmlConsoleDirective)
