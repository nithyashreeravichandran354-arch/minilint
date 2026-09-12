"""Ties every rule together into a single entry point: parse a file, run
every rule over its AST, return sorted diagnostics."""

import ast
from pathlib import Path

from .diagnostics import Diagnostic
from .rules import ALL_RULES


def lint_source(source: str) -> list[Diagnostic]:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [
            Diagnostic(
                line=exc.lineno or 0,
                col=exc.offset or 0,
                rule_id="ML000",
                message=f"syntax error: {exc.msg}",
            )
        ]

    diagnostics: list[Diagnostic] = []
    for rule_cls in ALL_RULES:
        rule = rule_cls()
        diagnostics.extend(rule.check(tree))
    return sorted(diagnostics)


def lint_file(path: str) -> list[Diagnostic]:
    source = Path(path).read_text()
    return lint_source(source)
