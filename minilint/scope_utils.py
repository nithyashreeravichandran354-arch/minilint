"""Helpers for walking a function body while respecting scope boundaries.

Plain ``ast.walk`` recurses into *everything*, including nested function
and lambda bodies, which have their own scope. Several rules (unused
variables, shadowing, use-before-assignment) need to reason about a single
function's own local names, not the names of functions nested inside it.
"""

import ast

_SCOPE_BOUNDARIES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)


def iter_own_scope(node: ast.AST):
    """Yield every descendant of ``node`` that belongs to its own scope,
    i.e. stop descending at nested function/lambda boundaries (their names
    are still yielded, since defining them *is* a binding in the outer
    scope, but their bodies/args are not).
    """
    for child in ast.iter_child_nodes(node):
        if isinstance(child, _SCOPE_BOUNDARIES):
            # The def/lambda's own body and parameters belong to the new
            # scope, but a FunctionDef/AsyncFunctionDef node's *name* is a
            # binding in the enclosing scope (like `inner = <function>`),
            # so we still surface a synthetic Name store for it here.
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield _FunctionBinding(child)
            continue
        yield child
        yield from iter_own_scope(child)


class _FunctionBinding(ast.AST):
    """A stand-in Name(ctx=Store) node representing a `def name(...): ...`
    binding its name in the enclosing scope, without exposing the
    function's internal body/params to the caller's scope walk."""

    _fields = ()

    def __init__(self, func_def):
        self.id = func_def.name
        self.ctx = ast.Store()
        self.lineno = func_def.lineno
        self.col_offset = func_def.col_offset


# Make isinstance(x, ast.Name) checks in callers work uniformly by
# registering the stand-in as a Name subclass would; simpler: callers
# should check `isinstance(x, (ast.Name, _FunctionBinding))`. We expose
# a tuple for that purpose.
NAME_LIKE = (ast.Name, _FunctionBinding)
