from __future__ import annotations

from ast import Attribute, Call, ImportFrom, Name
from typing import TYPE_CHECKING

from scrapy_lint.finders.unsupported import (
    VALID_REQUEST_IMPORT_PATHS,
    import_path_from_attribute,
)
from scrapy_lint.issues import DEPRECATED_METHOD, Issue, Pos

if TYPE_CHECKING:
    from ast import AST, expr
    from collections.abc import Generator

FROM_RESPONSE_DETAIL = "deprecated in scrapy 2.16.0; use form2request instead"


class DeprecatedMethodIssueFinder:
    """Report calls to deprecated Scrapy methods.

    Handles ``ImportFrom`` nodes to learn the local names of the classes those
    methods belong to, and ``Call`` nodes to report the calls themselves.
    """

    def __init__(self) -> None:
        self.form_request_names = {"FormRequest"}

    def __call__(self, node: AST) -> Generator[Issue]:
        if isinstance(node, ImportFrom):
            self.track_import(node)
            return
        assert isinstance(node, Call)
        func = node.func
        if (
            isinstance(func, Attribute)
            and func.attr == "from_response"
            and self.is_form_request(func.value)
        ):
            yield Issue(DEPRECATED_METHOD, Pos.from_node(node), FROM_RESPONSE_DETAIL)

    def track_import(self, node: ImportFrom) -> None:
        if not node.module or node.module.split(".")[0] != "scrapy":
            return
        for alias in node.names:
            if alias.name == "FormRequest" and alias.asname:
                self.form_request_names.add(alias.asname)

    def is_form_request(self, node: expr) -> bool:
        if isinstance(node, Name):
            return node.id in self.form_request_names
        return (
            isinstance(node, Attribute)
            and node.attr == "FormRequest"
            and import_path_from_attribute(node.value)
            in VALID_REQUEST_IMPORT_PATHS["FormRequest"]
        )
