"""ML005: a nested function that assigns a name already bound in one of
its *enclosing* function scopes silently shadows it, which is a common
source of "why didn't my outer variable change" bugs.

Note the scoping rule this deliberately gets right: a name defined in a
*sibling* nested function (or in a scope that isn't actually enclosing the
one being checked) must NOT be reported as shadowed -- only names visible
via Python's real lexical scoping (the chain of enclosing function defs)
count.
"""

import ast

from ..diagnostics import Diagnostic
from ..scope_utils import iter_own_scope, NAME_LIKE


class ShadowedVariableRule:
    rule_id = "ML005"

    def check(self, tree: ast.AST) -> list[Diagnostic]:
        diags = []
        self._walk(tree, scope_stack=[])
        diags.extend(self._diags)
        return diags

    def __init__(self):
        self._diags: list[Diagnostic] = []

    def _walk(self, node: ast.AST, scope_stack: list[set]):
        """Recurse over the whole tree; scope_stack holds the set of names
        locally assigned in each *enclosing* function, outermost first.
        Only actual FunctionDef/AsyncFunctionDef nodes push a new scope.
        """
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            own_names = self._own_local_names(node)
            for name, first_node in own_names.items():
                for enclosing in scope_stack:
                    if name in enclosing:
                        self._diags.append(
                            Diagnostic(
                                line=first_node.lineno,
                                col=first_node.col_offset,
                                rule_id=self.rule_id,
                                message=f"'{name}' shadows a variable of the same "
                                "name from an enclosing function",
                            )
                        )
                        break
            new_stack = scope_stack + [set(own_names)]
            for child in ast.iter_child_nodes(node):
                self._walk(child, new_stack)
        else:
            for child in ast.iter_child_nodes(node):
                self._walk(child, scope_stack)

    @staticmethod
    def _own_local_names(func) -> dict[str, ast.AST]:
        names: dict[str, ast.AST] = {}
        params = (
            func.args.args
            + func.args.posonlyargs
            + func.args.kwonlyargs
        )
        for p in params:
            names.setdefault(p.arg, func)

        declared_nonlocal_or_global: set[str] = set()
        for node in iter_own_scope(func):
            if isinstance(node, (ast.Global, ast.Nonlocal)):
                declared_nonlocal_or_global.update(node.names)

        for node in iter_own_scope(func):
            if isinstance(node, NAME_LIKE) and isinstance(node.ctx, ast.Store):
                if node.id in declared_nonlocal_or_global:
                    continue  # explicitly refers to an outer binding, not a new one
                names.setdefault(node.id, node)
        return names
