"""ML001: bare `except:` clauses swallow every exception, including
KeyboardInterrupt and SystemExit, and hide bugs. Flag them."""

import ast

from ..diagnostics import Diagnostic


class BareExceptRule:
    rule_id = "ML001"

    def check(self, tree: ast.AST) -> list[Diagnostic]:
        diags = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                diags.append(
                    Diagnostic(
                        line=node.lineno,
                        col=node.col_offset,
                        rule_id=self.rule_id,
                        message="bare 'except:' catches all exceptions; "
                        "catch a specific exception type instead",
                    )
                )
        return diags
