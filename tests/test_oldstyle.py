from __future__ import annotations

from . import NO_ISSUE, Cases, ExpectedIssue, File, cases
from .helpers import check_project

PATH = "a.py"
CASES: Cases = (
    *(
        (
            File(code, path=PATH),
            issues,
            {},
        )
        for code, issues in (
            # SCP03: improper response URL join
            *(
                (
                    code,
                    ExpectedIssue(
                        message="SCP03 improper response URL join",
                        column=column,
                        path=PATH,
                    ),
                )
                for code, column in (
                    ('urljoin(response.url, "/foo")', 0),
                    ('url = urljoin(response.url, "/foo")', 6),
                )
            ),
            # SCP03: improper response URL join (no issue)
            *(
                (code, NO_ISSUE)
                for code in (
                    'response.urljoin("/foo")',
                    "url = urljoin()",
                    'urljoin(x, "/foo")',
                    'urljoin(x.y.z, "/foo")',
                )
            ),
            # SCP04: improper response selector
            *(
                (
                    code,
                    ExpectedIssue(
                        message="SCP04 improper response selector",
                        path=PATH,
                    ),
                )
                for code in (
                    "sel = Selector(response)",
                    'sel = Selector(response, type="html")',
                    'sel = Selector(response=response, type="html")',
                    "sel = Selector(response=response)",
                    "sel = Selector(text=response.text)",
                    "sel = Selector(text=response.body)",
                    "sel = Selector(text=response.body_as_unicode())",
                    'sel = Selector(text=response.text, type="html")',
                )
            ),
            # SCP04: improper response selector (no issue)
            *(
                (code, NO_ISSUE)
                for code in (
                    "sel = Selector(get_text())",
                    "sel = Selector(self.get_text())",
                )
            ),
            # SCP06: improper first match extraction
            *(
                (
                    code,
                    ExpectedIssue(
                        message="SCP06 improper first match extraction",
                        path=PATH,
                    ),
                )
                for code in (
                    'response.css("*")[0].extract()',
                    'response.xpath("//*")[0].extract()',
                    'response.css("*").extract()[0]',
                    'response.xpath("//*").extract()[0]',
                    'response.css("*").getall()[0]',
                    'response.xpath("//*")[0].get()',
                    'response.css("*").extract_first()',
                    'response.xpath("//*").extract_first()',
                    'response.css("*").extract_first(default="")',
                )
            ),
            # SCP06: improper first match extraction (no issue)
            *(
                (code, NO_ISSUE)
                for code in (
                    "selector.extract()",
                    "selector.extract_first()",
                    "selector[0].extract()",
                    'response.jmespath("*")[0].extract()',
                    'response.jmespath("*").extract()[0]',
                    'response.jmespath("*").extract_first()',
                    'response.css("*")[1].extract()',
                    # Non-constant subscripts
                    'response.css("*")[n].extract()',
                )
            ),
            # SCP48: old selector getter
            *(
                (
                    code,
                    ExpectedIssue(
                        message="SCP48 old selector getter",
                        path=PATH,
                    ),
                )
                for code in (
                    'response.css("*").extract()',
                    'response.xpath("//*").extract()',
                    'response.css("*").css("a").extract()',
                    # Indexes other than the first one are not SCP06.
                    'response.css("*").extract()[1]',
                    'response.css("*").extract()[n]',
                )
            ),
            # SCP48: old selector getter (no issue)
            *(
                (code, NO_ISSUE)
                for code in (
                    'response.jmespath("*").extract()',
                    'response.css("*").getall()',
                )
            ),
            # SCP49: absolute XPath in nested selector
            *(
                (
                    code,
                    ExpectedIssue(
                        message="SCP49 absolute XPath in nested selector",
                        column=column,
                        path=PATH,
                    ),
                )
                for code, column in (
                    ('response.css("div").xpath("//a")', 26),
                    ('response.xpath("//div").xpath("/a")', 30),
                    ('response.css("div")[0].xpath("//a")', 29),
                )
            ),
            # SCP49: absolute XPath in nested selector (no issue)
            *(
                (code, NO_ISSUE)
                for code in (
                    'response.xpath("//a")',
                    'selector.xpath("//a")',
                    'response.css("div").xpath(".//a")',
                    'response.css("div").xpath(query)',
                    'response.css("div").xpath()',
                )
            ),
        )
    ),
)


@cases(CASES)
def test(
    files: File | list[File],
    expected: ExpectedIssue | list[ExpectedIssue] | None,
    options,
):
    check_project(files, expected, options)
