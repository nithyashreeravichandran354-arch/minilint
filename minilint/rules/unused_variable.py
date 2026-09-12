"""ML004: local variables that are assigned but never read are almost
always dead code or a typo (e.g. assigning to the wrong name)."""

import ast

from ..diagnostics import Diagnostic
from ..scope_utils import iter_own_scope, NAME_LIKE


class UnusedVariableRule:
    rule_id = "ML004"

    def check(self, tree: ast.AST) -> list[Diagnostic]:
        diags = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                diags.extend(self._check_function(node))
        return diags

    def _check_function(self, func) -> list[Diagnostic]:
        assigned: dict[str, ast.AST] = {}
        used: set[str] = set()
        globals_or_nonlocal: set[str] = set()

        params = {a.arg for a in func.args.args}
        params |= {a.arg for a in func.args.posonlyargs}
        params |= {a.arg for a in func.args.kwonlyargs}
        if func.args.vararg:
            params.add(func.args.vararg.arg)
        if func.args.kwarg:
            params.add(func.args.kwarg.arg)

        for stmt in iter_own_scope(func):
            if isinstance(stmt, ast.Global) or isinstance(stmt, ast.Nonlocal):
                globals_or_nonlocal.update(stmt.names)
            elif isinstance(stmt, NAME_LIKE):
                if isinstance(stmt.ctx, ast.Store) and stmt.id not in assigned:
                    assigned[stmt.id] = stmt
                elif isinstance(stmt.ctx, ast.Load):
                    used.add(stmt.id)

        # A variable that looks unused in this scope may actually be
        # captured by a nested function via `nonlocal`. That's a genuine
        # use of the binding (just from inside a child scope), so scan the
        # whole subtree -- not just this function's own scope -- for
        # `nonlocal` declarations and count those names as used here too.
        for node in ast.walk(func):
            if isinstance(node, ast.Nonlocal):
                used.update(node.names)

        diags = []
        for name, node in assigned.items():
            if name in params or name in globals_or_nonlocal or name in used:
                continue
            if name.startswith("_"):
                continue  # conventional "intentionally unused" marker
            diags.append(
                Diagnostic(
                    line=node.lineno,
                    col=node.col_offset,
                    rule_id=self.rule_id,
                    message=f"local variable '{name}' is assigned but never used",
                )
            )
        return diags
