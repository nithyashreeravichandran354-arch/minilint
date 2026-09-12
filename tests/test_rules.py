from pathlib import Path

from minilint.engine import lint_source, lint_file

SAMPLES = Path(__file__).parent.parent / "samples"


def rule_ids(diags):
    return sorted(d.rule_id for d in diags)


def test_bare_except_flagged():
    src = "try:\n    pass\nexcept:\n    pass\n"
    diags = lint_source(src)
    assert "ML001" in rule_ids(diags)


def test_specific_except_not_flagged():
    src = "try:\n    pass\nexcept ValueError:\n    pass\n"
    diags = lint_source(src)
    assert "ML001" not in rule_ids(diags)


def test_none_equality_flagged():
    src = "def f(x):\n    return x == None\n"
    diags = lint_source(src)
    assert "ML002" in rule_ids(diags)


def test_none_identity_not_flagged():
    src = "def f(x):\n    return x is None\n"
    diags = lint_source(src)
    assert "ML002" not in rule_ids(diags)


def test_dead_code_after_return():
    src = "def f():\n    return 1\n    print('dead')\n"
    diags = [d for d in lint_source(src) if d.rule_id == "ML003"]
    assert len(diags) == 1
    assert diags[0].line == 3


def test_no_dead_code_false_positive_across_branches():
    src = (
        "def f(x):\n"
        "    if x:\n"
        "        return 1\n"
        "    return 2\n"
    )
    diags = [d for d in lint_source(src) if d.rule_id == "ML003"]
    assert diags == []


def test_unused_variable_flagged():
    src = "def f():\n    x = 1\n    return 2\n"
    diags = [d for d in lint_source(src) if d.rule_id == "ML004"]
    assert len(diags) == 1


def test_used_variable_not_flagged():
    src = "def f():\n    x = 1\n    return x\n"
    diags = [d for d in lint_source(src) if d.rule_id == "ML004"]
    assert diags == []


def test_underscore_convention_not_flagged():
    src = "def f():\n    _ignored = 1\n    return 2\n"
    diags = [d for d in lint_source(src) if d.rule_id == "ML004"]
    assert diags == []


def test_shadowed_variable_flagged():
    src = (
        "def outer():\n"
        "    x = 1\n"
        "    def inner():\n"
        "        x = 2\n"
        "        return x\n"
        "    return inner\n"
    )
    diags = [d for d in lint_source(src) if d.rule_id == "ML005"]
    assert len(diags) == 1


def test_sibling_scopes_not_flagged_as_shadowing():
    """Regression test: a name used in one nested function must not be
    reported as shadowed just because a *sibling* nested function also
    happens to use that name -- only real lexical enclosure counts."""
    src = (
        "def outer():\n"
        "    def a():\n"
        "        x = 1\n"
        "        return x\n"
        "    def b():\n"
        "        x = 2\n"
        "        return x\n"
        "    return a() + b()\n"
    )
    diags = [d for d in lint_source(src) if d.rule_id == "ML005"]
    assert diags == []


def test_nonlocal_not_flagged_as_shadowing():
    src = (
        "def outer():\n"
        "    count = 0\n"
        "    def inner():\n"
        "        nonlocal count\n"
        "        count = count + 1\n"
        "        return count\n"
        "    return inner\n"
    )
    diags = [d for d in lint_source(src) if d.rule_id == "ML005"]
    assert diags == []


def test_defining_nested_function_is_not_use_before_assignment():
    """Regression test: naming and defining a nested function binds its
    name immediately; calling it afterwards is not a use-before-assign."""
    src = (
        "def outer():\n"
        "    def inner():\n"
        "        return 1\n"
        "    return inner()\n"
    )
    diags = [d for d in lint_source(src) if d.rule_id == "ML006"]
    assert diags == []


def test_use_before_assignment_flagged():
    src = "def f():\n    print(x)\n    x = 1\n"
    diags = [d for d in lint_source(src) if d.rule_id == "ML006"]
    assert len(diags) == 1


def test_parameters_never_flagged_as_use_before_assignment():
    src = "def f(x):\n    print(x)\n    x = 1\n"
    diags = [d for d in lint_source(src) if d.rule_id == "ML006"]
    assert diags == []


def test_buggy_sample_has_exactly_six_issues_one_per_rule():
    diags = lint_file(str(SAMPLES / "buggy.py"))
    ids = rule_ids(diags)
    assert ids == ["ML001", "ML002", "ML003", "ML004", "ML005", "ML006"]


def test_clean_sample_has_zero_issues():
    diags = lint_file(str(SAMPLES / "clean.py"))
    assert diags == []
