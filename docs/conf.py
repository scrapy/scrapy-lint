from pathlib import Path

from scrapy_lint.data.packages import PACKAGES

project = "scrapy-lint"
project_copyright = "Valdir Stumm Junior"
author = "Valdir Stumm Junior"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx_rtd_dark_mode",
    "sphinx_scrapy",
]

exclude_patterns = ["_package_versions.rst"]

html_theme = "sphinx_rtd_theme"
default_dark_mode = False

scrapy_intersphinx_enable = [
    "shub",
    "scrapy-poet",
    "scrapy-zyte-api",
    "zyte",
]

PACKAGE_DISPLAY_NAMES = {"scrapy": "Scrapy"}


def _write_package_versions_table(app):
    lines = [
        ".. list-table::",
        "   :header-rows: 1",
        "",
        "   * - Package",
        "     - Minimum version",
    ]
    for name, package in PACKAGES.items():
        if package.lowest_supported_version is None:
            continue
        display_name = PACKAGE_DISPLAY_NAMES.get(name, name)
        lines.append(f"   * - {display_name}")
        lines.append(f"     - {package.lowest_supported_version}")
    path = Path(app.srcdir) / "_package_versions.rst"
    path.write_text("\n".join(lines) + "\n")


def setup(app):
    app.connect("builder-inited", _write_package_versions_table)
