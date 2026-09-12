"""ML003: statements that appear after an unconditional `return`, `raise`,
`break`, or `continue` in the *same* block can never execute."""

import ast

from ..diagnostics import Diagnostic

_TERMINATORS = (ast.Return, ast.Raise, ast.Break, ast.Continue)


class DeadCodeRule:
    rule_id = "ML003"

    def check(self, tree: ast.AST) -> list[Diagnostic]:
        diags = []
        for node in ast.walk(tree):
            for block in self._blocks_of(node):
                diags.extend(self._check_block(block))
        return diags

    @staticmethod
    def _blocks_of(node: ast.AST):
        """Yield every statement list ("block") directly owned by node."""
        for field in ("body", "orelse", "finalbody"):
            block = getattr(node, field, None)
            if isinstance(block, list) and block and isinstance(block[0], ast.stmt):
                yield block

    def _check_block(self, block: list[ast.stmt]) -> list[Diagnostic]:
        diags = []
        terminated_at = None
        for stmt in block:
            if terminated_at is not None:
                diags.append(
                    Diagnostic(
                        line=stmt.lineno,
                        col=stmt.col_offset,
                        rule_id=self.rule_id,
                        message=f"unreachable code (line {terminated_at} always "
                        "returns, raises, breaks, or continues first)",
                    )
                )
            if isinstance(stmt, _TERMINATORS) and terminated_at is None:
                terminated_at = stmt.lineno
        return diags
