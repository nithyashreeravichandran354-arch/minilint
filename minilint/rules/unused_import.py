"""ML009: an imported name that is never referenced anywhere else in the
module is dead weight -- it slows down import time for no benefit, and
often signals a half-finished refactor (the code that used it was deleted,
the import wasn't).

Known blind spot, documented rather than hidden (in the same spirit as
ML006's flow-insensitivity note): a name used only inside a string-based
type annotation (`x: "SomeType"`) or inside `exec`/`eval` is not detected
as a use, since that would require evaluating strings as code. Names
re-exported via `__all__` *are* recognised as used.
"""

import ast

from ..diagnostics import Diagnostic


class UnusedImportRule:
    rule_id = "ML009"

    def check(self, tree: ast.AST) -> list[Diagnostic]:
        imports = self._collect_imports(tree)
        if not imports:
            return []

        used = {
            node.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
        }
        used |= self._names_in_dunder_all(tree)

        diags = []
        seen: set[str] = set()
        for bound_name, node in imports:
            if bound_name in seen:
                continue
            seen.add(bound_name)
            if bound_name not in used:
                diags.append(
                    Diagnostic(
                        line=node.lineno,
                        col=node.col_offset,
                        rule_id=self.rule_id,
                        message=f"'{bound_name}' is imported but never used",
                    )
                )
        return diags

    @staticmethod
    def _collect_imports(tree) -> list[tuple[str, ast.AST]]:
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    bound = alias.asname or alias.name.split(".")[0]
                    imports.append((bound, node))
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    bound = alias.asname or alias.name
                    imports.append((bound, node))
        return imports

    @staticmethod
    def _names_in_dunder_all(tree) -> set[str]:
        names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets
            ):
                if isinstance(node.value, (ast.List, ast.Tuple, ast.Set)):
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            names.add(elt.value)
        return names
