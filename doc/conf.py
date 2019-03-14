#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# tbot documentation build configuration file, created by
# sphinx-quickstart on Tue Aug 28 11:57:52 2018.
from recommonmark.parser import CommonMarkParser

# -- General configuration ------------------------------------------------
needs_sphinx = '1.6'
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.viewcode',
]
templates_path = ['_templates']

source_parsers = {
    '.md': CommonMarkParser,
}
source_suffix = ['.rst', '.md']

master_doc = 'index'

# General information about the project.
project = 'tbot'
copyright = '2018, Rahix'
author = 'Rahix'

# The version info for the project you're documentingimport subprocess
import subprocess
release = subprocess.run(
    ["git", "describe", "--long"],
    stdout=subprocess.PIPE
).stdout.decode().strip()[1:]
version = release

language = None
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The name of the Pygments (syntax highlighting) style to use.
if tags.has("pygments-light"):
    pygments_style = 'default'
else:
    pygments_style = 'monokai'

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True

autoclass_content = 'both'
autodoc_member_order = "bysource"
autodoc_default_options = {
    'show-inheritance': None,
}

# -- Options for HTML output ----------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_logo = '_static/tbot-logo-white.png'
html_theme_options = {
    'logo_only': True,
}
html_static_path = ['_static']
# refs: http://alabaster.readthedocs.io/en/latest/installation.html#sidebars
html_sidebars = {
    '**': [
        'relations.html',  # needs 'show_related': True theme option to display
        'searchbox.html',
    ]
}


# -- Options for HTMLHelp output ------------------------------------------
# Output file base name for HTML help builder.
htmlhelp_basename = 'tbotdoc'


# -- Options for LaTeX output ---------------------------------------------
latex_logo = '_static/tbot-logo.png'
latex_elements = {
    'papersize': 'a4paper',
    # 'pointsize': '10pt',
    'preamble': r"""
\usepackage{alltt}

\DeclareUnicodeCharacter{1F8A5}{$\Rightarrow$}
""",

    # Latex figure (float) alignment
    # 'figure_align': 'htbp',
}

latex_documents = [
    (master_doc, 'tbot.tex', 'tbot Documentation',
     'Rahix', 'manual'),
]


# -- Options for manual page output ---------------------------------------
man_pages = [
    (master_doc, 'tbot', 'tbot Documentation',
     [author], 1)
]


# -- Options for Texinfo output -------------------------------------------
texinfo_documents = [
    (master_doc, 'tbot', 'tbot Documentation',
     author, 'tbot', 'One line description of project.',
     'Miscellaneous'),
]


# Intersphinx Config
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'paramiko': ('http://docs.paramiko.org/en/2.4', None),
}


# -- html-console extension -----------------------------------------------
from docutils.parsers import rst
from docutils import nodes
import re

def setup(app):
    app.add_directive("html-console", HtmlConsoleDirective)


class HtmlConsoleDirective(rst.Directive):
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    option_spec = {}

    pat_pre = re.compile(r'</?pre>')
    pat_color = re.compile(r'<font color="#([A-Z0-9]+)">(.+?)</font>')
    pat_bold = re.compile(r'<b>(.+?)</b>')

    def run(self):
        self.assert_has_content()
        text = '\n'.join(self.content)

        gen = []
        # Add html version
        html_text = '<div class="highlight">\n' + text + '\n</div>'
        gen.append(nodes.raw(text, html_text, format="html"))

        # Add latex version
        latex_text = "\\begin{sphinxVerbatim}[commandchars=\\\\\\{\\}]\n"
        transformed = text
        transformed = transformed.replace("\\", "\\textbackslash{}")
        transformed = self.pat_pre.sub('', transformed)
        transformed = self.pat_color.sub(r'\\textcolor[HTML]{\1}{\2}', transformed)
        transformed = self.pat_bold.sub(r'\\textbf{\1}', transformed)
        transformed = transformed.replace("&lt;", "<")
        transformed = transformed.replace("&gt;", ">")
        transformed = transformed.replace("&apos;", r"\textsc{\char39}")
        transformed = transformed.replace("&quot;", '"')
        latex_text += transformed
        latex_text += "\n\\end{sphinxVerbatim}"
        gen.append(nodes.raw(text, latex_text, format="latex"))

        return gen


# Fix instance variables being cross-referenced
from sphinx.util.docfields import TypedField
from sphinx import addnodes

def patched_make_field(self,
                       types,     # type: Dict[unicode, List[nodes.Node]]
                       domain,    # type: unicode
                       items,     # type: Tuple
                       env=None,  # type: BuildEnvironment
                      ):
    # type: (...) -> nodes.field
    def handle_item(fieldarg, content):
        # type: (unicode, unicode) -> nodes.paragraph
        par = nodes.paragraph()
        par += addnodes.literal_strong('', fieldarg)  # Patch: this line added
        # par.extend(self.make_xrefs(self.rolename, domain, fieldarg,
        #                            addnodes.literal_strong, env=env))
        if fieldarg in types:
            par += nodes.Text(' (')
            # NOTE: using .pop() here to prevent a single type node to be
            # inserted twice into the doctree, which leads to
            # inconsistencies later when references are resolved
            fieldtype = types.pop(fieldarg)
            if len(fieldtype) == 1 and isinstance(fieldtype[0], nodes.Text):
                typename = u''.join(n.astext() for n in fieldtype)
                par.extend(self.make_xrefs(self.typerolename, domain, typename,
                                           addnodes.literal_emphasis, env=env))
            else:
                par += fieldtype
            par += nodes.Text(')')
        par += nodes.Text(' -- ')
        par += content
        return par

    fieldname = nodes.field_name('', self.label)
    if len(items) == 1 and self.can_collapse:
        fieldarg, content = items[0]
        bodynode = handle_item(fieldarg, content)
    else:
        bodynode = self.list_type()
        for fieldarg, content in items:
            bodynode += nodes.list_item('', handle_item(fieldarg, content))
    fieldbody = nodes.field_body('', bodynode)
    return nodes.field('', fieldname, fieldbody)

TypedField.make_field = patched_make_field
