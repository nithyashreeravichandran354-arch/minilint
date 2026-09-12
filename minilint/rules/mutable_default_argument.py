"""ML007: a mutable object (list/dict/set literal, or a call to
list()/dict()/set()) used as a parameter default is evaluated exactly once,
at function-definition time -- not on every call. Every call that doesn't
pass its own value for that parameter shares the *same* object, so a
mutation made during one call is silently visible on the next one.
"""

import ast

from ..diagnostics import Diagnostic

_MUTABLE_FACTORY_CALLS = {"list", "dict", "set"}


class MutableDefaultArgumentRule:
    rule_id = "ML007"

    def check(self, tree: ast.AST) -> list[Diagnostic]:
        diags = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                diags.extend(self._check_function(node))
        return diags

    def _check_function(self, func) -> list[Diagnostic]:
        diags = []
        defaults = list(func.args.defaults) + [
            d for d in func.args.kw_defaults if d is not None
        ]
        for default in defaults:
            if self._is_mutable_literal(default):
                diags.append(
                    Diagnostic(
                        line=default.lineno,
                        col=default.col_offset,
                        rule_id=self.rule_id,
                        message=(
                            f"mutable default argument in '{func.name}'; it is "
                            "created once and shared across every call that "
                            "doesn't override it -- use None and create the "
                            "value inside the function body instead"
                        ),
                    )
                )
        return diags

    @staticmethod
    def _is_mutable_literal(node: ast.AST) -> bool:
        if isinstance(node, (ast.List, ast.Dict, ast.Set)):
            return True
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in _MUTABLE_FACTORY_CALLS
            and not node.args
            and not node.keywords
        ):
            return True
        return False
