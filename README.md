# minilint

A small, from-scratch static analysis tool for Python, built to demonstrate
core static-analysis concepts on real code rather than just describe them:
AST traversal, lexical scope modelling, and dataflow analysis (including
being explicit about where a cheap analysis is *unsound*, rather than
hiding it).

## What it checks

| Rule ID | Name | What it catches |
|---|---|---|
| ML001 | bare-except | `except:` with no exception type |
| ML002 | none-comparison | `x == None` / `x != None` instead of `is` / `is not` |
| ML003 | dead-code | statements after an unconditional `return`/`raise`/`break`/`continue` |
| ML004 | unused-variable | a local variable assigned but never read (closure captures via `nonlocal` count as a read) |
| ML005 | shadowed-variable | a nested function rebinding a name from a *real* enclosing scope (not a sibling scope) |
| ML006 | use-before-assignment | a name read before its first assignment, by source order, within a function |

Rules ML001–ML003 are simple, well-known syntactic lint checks. ML004–ML006
require actual scope modelling: correctly walking a function's *own* scope
while not reaching into (ML004, ML006) or wrongly comparing against (ML005)
nested function scopes that don't lexically enclose the code being checked.

### A documented unsoundness, on purpose

ML006 is **flow-insensitive**: it compares source line/column order, not
real control flow. It will miss bugs hidden behind conditionals and can
theoretically false-positive on unusual closures. A sound version would
need a control-flow graph and reaching-definitions analysis. The rule's
docstring (`minilint/rules/use_before_assignment.py`) spells this out
rather than presenting the check as more rigorous than it is — that
tradeoff, and being honest about it, is itself the point of including it.

## Usage

```bash
python -m minilint path/to/file.py [more_files.py ...]
```

Example:

```bash
$ python -m minilint samples/buggy.py
samples/buggy.py:8:4: [ML001] bare 'except:' catches all exceptions; catch a specific exception type instead
samples/buggy.py:13:7: [ML002] comparison to None should use 'is', not '==' / '!='
samples/buggy.py:21:8: [ML003] unreachable code (line 20 always returns, raises, breaks, or continues first)
samples/buggy.py:27:4: [ML004] local variable 'unused' is assigned but never used
samples/buggy.py:38:8: [ML005] 'count' shadows a variable of the same name from an enclosing function
samples/buggy.py:45:24: [ML006] 'greeting' is used here but not assigned until later in the function (flow-insensitive check: see rule docstring for limitations)

6 issue(s) found.
```

`samples/clean.py` is the same file with every issue fixed, to confirm the
tool has zero false positives on valid code.

## Running the tests

```bash
pip install pytest
pytest tests/ -v
```

(17 tests: one or two per rule for the true-positive/true-negative case,
plus dedicated regression tests for the two scoping bugs found and fixed
during development — see below — and end-to-end checks against both
sample files.)

## Design notes / things that were genuinely tricky

- **Scope-aware traversal.** `ast.walk` recurses into everything, including
  nested function and lambda bodies. `minilint/scope_utils.py` implements
  `iter_own_scope`, which stops at scope boundaries so that a rule
  reasoning about one function doesn't accidentally see variables that
  belong to a function nested inside it.
- **Two real bugs found and fixed while building this:**
  1. The shadowing rule initially reached into arbitrarily nested scopes
     when deciding what counted as "shadowed," which meant it could flag a
     variable in one nested function as shadowing a same-named variable in
     an unrelated *sibling* nested function. Fixed by walking an explicit
     enclosing-scope stack instead of a flat name set.
  2. The use-before-assignment rule initially flagged calling a nested
     function as "using it before assignment," because it didn't treat
     `def inner(): ...` as binding the name `inner` at that point (the way
     `inner = <a function>` would). Fixed by treating a `FunctionDef`/
     `AsyncFunctionDef` node as a synthetic store of its own name in the
     enclosing scope, without exposing its internal body to that scope's
     walk.
  3. Similarly, a variable that looks unused in a function can actually be
     captured by a nested closure via `nonlocal`; the unused-variable rule
     now treats a `nonlocal` declaration for a name anywhere in the
     subtree as evidence the enclosing binding is used.

## Project layout

```
minilint/
  diagnostics.py       # shared Diagnostic dataclass
  scope_utils.py        # scope-respecting AST traversal helper
  engine.py              # parses a file, runs every rule, returns sorted diagnostics
  cli.py / __main__.py   # `python -m minilint ...`
  rules/
    bare_except.py
    none_comparison.py
    dead_code.py
    unused_variable.py
    shadowed_variable.py
    use_before_assignment.py
samples/
  buggy.py               # one deliberate bug per rule
  clean.py               # same file, all fixed -- zero false positives
tests/
  test_rules.py
```
