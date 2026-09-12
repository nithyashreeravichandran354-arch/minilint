"""ML008: a function with a long parameter list is harder to call
correctly and harder to test in isolation -- callers tend to pass
positional arguments in the wrong order, and each new optional parameter
multiplies the number of behaviourally-distinct call sites. This is a
threshold heuristic, not a hard rule: some domains genuinely need more
parameters, so the limit is intentionally a class attribute rather than a
hardcoded constant, so a project can tune it.

`self`/`cls` are excluded from the count -- they are not part of the
caller-facing signature.
"""

import ast

from ..diagnostics import Diagnostic

_DEFAULT_MAX_ARGS = 5
_IMPLICIT_FIRST_PARAMS = {"self", "cls"}


class TooManyArgumentsRule:
    rule_id = "ML008"

    def __init__(self, max_args: int = _DEFAULT_MAX_ARGS):
        self.max_args = max_args

    def check(self, tree: ast.AST) -> list[Diagnostic]:
        diags = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                diag = self._check_function(node)
                if diag is not None:
                    diags.append(diag)
        return diags

    def _check_function(self, func):
        positional = list(func.args.posonlyargs) + list(func.args.args)
        count = len(positional) + len(func.args.kwonlyargs)

        if positional and positional[0].arg in _IMPLICIT_FIRST_PARAMS:
            count -= 1

        if count <= self.max_args:
            return None

        return Diagnostic(
            line=func.lineno,
            col=func.col_offset,
            rule_id=self.rule_id,
            message=(
                f"'{func.name}' has {count} parameters (max {self.max_args}); "
                "consider grouping related parameters into a dataclass or dict"
            ),
        )
