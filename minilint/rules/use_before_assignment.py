"""ML006: a local variable is read at a source position earlier than any
assignment to it within the same function.

LIMITATION (documented honestly, not swept under the rug): this analysis
is *flow-insensitive* — it only compares source line numbers, not actual
control flow. It will therefore:
  * MISS real bugs where a variable is only assigned inside a branch that
    doesn't execute (e.g. `if False: x = 1` followed by `use(x)`), because
    the assignment's line number still comes "before" the use.
  * FALSE-POSITIVE on code that is actually fine at runtime if a use
    textually precedes its assignment but the assignment always executes
    first at runtime in a way line order doesn't capture (this is rare in
    straight-line code but possible with e.g. recursive-looking closures).
A precise version would require a real control-flow graph and reaching
-definitions dataflow analysis; this rule trades that precision for
simplicity, and says so instead of pretending to be sound.
"""

import ast

from ..diagnostics import Diagnostic
from ..scope_utils import iter_own_scope, NAME_LIKE


class UseBeforeAssignmentRule:
    rule_id = "ML006"

    def check(self, tree: ast.AST) -> list[Diagnostic]:
        diags = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                diags.extend(self._check_function(node))
        return diags

    def _check_function(self, func) -> list[Diagnostic]:
        params = {
            a.arg
            for a in (func.args.args + func.args.posonlyargs + func.args.kwonlyargs)
        }
        if func.args.vararg:
            params.add(func.args.vararg.arg)
        if func.args.kwarg:
            params.add(func.args.kwarg.arg)

        globals_or_nonlocal: set[str] = set()
        events = []  # (lineno, col, kind, name) kind in {"store", "load"}

        for node in iter_own_scope(func):
            if isinstance(node, (ast.Global, ast.Nonlocal)):
                globals_or_nonlocal.update(node.names)
            elif isinstance(node, NAME_LIKE):
                kind = "store" if isinstance(node.ctx, ast.Store) else (
                    "load" if isinstance(node.ctx, ast.Load) else None
                )
                if kind:
                    events.append((node.lineno, node.col_offset, kind, node.id))

        events.sort(key=lambda e: (e[0], e[1]))

        first_store_line: dict[str, int] = {}
        diags = []
        already_flagged: set[str] = set()

        for lineno, col, kind, name in events:
            if name in params or name in globals_or_nonlocal:
                continue
            if kind == "store":
                first_store_line.setdefault(name, lineno)
            else:  # load
                store_line = first_store_line.get(name)
                if store_line is None and name not in already_flagged:
                    # Could be a builtin, an import, or a genuine bug -- we
                    # only flag names that ARE assigned somewhere in this
                    # function later, to avoid drowning users in false
                    # positives on builtins/globals we didn't track.
                    if self._is_assigned_later(events, name):
                        diags.append(
                            Diagnostic(
                                line=lineno,
                                col=col,
                                rule_id=self.rule_id,
                                message=f"'{name}' is used here but not assigned "
                                "until later in the function (flow-insensitive "
                                "check: see rule docstring for limitations)",
                            )
                        )
                        already_flagged.add(name)
        return diags

    @staticmethod
    def _is_assigned_later(events, name) -> bool:
        return any(kind == "store" and n == name for _, _, kind, n in events)
