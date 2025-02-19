"""Sphinx extensions for performant PEP processing"""

from __future__ import annotations

from typing import TYPE_CHECKING

from docutils import nodes
from docutils.parsers.rst import states
from docutils.writers.html5_polyglot import HTMLTranslator
from sphinx import environment

from pep_sphinx_extensions.pep_processor.html import pep_html_builder
from pep_sphinx_extensions.pep_processor.html import pep_html_translator
from pep_sphinx_extensions.pep_processor.parsing import pep_parser
from pep_sphinx_extensions.pep_processor.parsing import pep_role
from pep_sphinx_extensions.pep_zero_generator.pep_index_generator import create_pep_zero

if TYPE_CHECKING:
    from sphinx.application import Sphinx

# Monkeypatch sphinx.environment.default_settings as Sphinx doesn't allow custom settings or Readers
# These settings should go in docutils.conf, but are overridden here for now so as not to affect
# pep2html.py
environment.default_settings |= {
    "pep_references": True,
    "rfc_references": True,
    "pep_base_url": "",
    "pep_file_url_template": "",
    "_disable_config": True,  # disable using docutils.conf whilst running both PEP generators
}

# TODO replace all inlined PEP and RFC strings with marked-up roles, disable pep_references and rfc_references and remove this monkey-patch
states.Inliner.pep_reference = lambda s, m, _l: [nodes.reference("", m.group(0), refuri=s.document.settings.pep_url.format(int(m.group("pepnum2"))))]


def _depart_maths():
    pass  # No-op callable for the type checker


def _update_config_for_builder(app: Sphinx):
    if app.builder.name == "dirhtml":
        environment.default_settings["pep_url"] = "../pep-{:0>4}"


def setup(app: Sphinx) -> dict[str, bool]:
    """Initialize Sphinx extension."""

    environment.default_settings["pep_url"] = "pep-{:0>4}.html"

    # Register plugin logic
    app.add_builder(pep_html_builder.FileBuilder, override=True)
    app.add_builder(pep_html_builder.DirectoryBuilder, override=True)
    app.add_source_parser(pep_parser.PEPParser)  # Add PEP transforms
    app.add_role("pep", pep_role.PEPRole(), override=True)  # Transform PEP references to links
    app.set_translator("html", pep_html_translator.PEPTranslator)  # Docutils Node Visitor overrides (html builder)
    app.set_translator("dirhtml", pep_html_translator.PEPTranslator)  # Docutils Node Visitor overrides (dirhtml builder)
    app.connect("env-before-read-docs", create_pep_zero)  # PEP 0 hook
    app.connect("builder-inited", _update_config_for_builder)  # Update configuration values for builder used

    # Mathematics rendering
    inline_maths = HTMLTranslator.visit_math, _depart_maths
    block_maths = HTMLTranslator.visit_math_block, _depart_maths
    app.add_html_math_renderer("maths_to_html", inline_maths, block_maths)  # Render maths to HTML

    # Parallel safety: https://www.sphinx-doc.org/en/master/extdev/index.html#extension-metadata
    return {"parallel_read_safe": True, "parallel_write_safe": True}
