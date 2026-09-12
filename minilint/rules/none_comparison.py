"""ML002: `x == None` / `x != None` should be `x is None` / `x is not None`.
Equality can be overridden by __eq__; identity comparison is what's meant."""

import ast

from ..diagnostics import Diagnostic


class NoneComparisonRule:
    rule_id = "ML002"

    def check(self, tree: ast.AST) -> list[Diagnostic]:
        diags = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            operands = [node.left, *node.comparators]
            for op, right in zip(node.ops, node.comparators):
                if not isinstance(op, (ast.Eq, ast.NotEq)):
                    continue
                left = operands[operands.index(right) - 1]
                if self._is_none(left) or self._is_none(right):
                    suggestion = "is" if isinstance(op, ast.Eq) else "is not"
                    diags.append(
                        Diagnostic(
                            line=node.lineno,
                            col=node.col_offset,
                            rule_id=self.rule_id,
                            message=f"comparison to None should use '{suggestion}', "
                            "not '==' / '!='",
                        )
                    )
        return diags

    @staticmethod
    def _is_none(node: ast.AST) -> bool:
        return isinstance(node, ast.Constant) and node.value is None
