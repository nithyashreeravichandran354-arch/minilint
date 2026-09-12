"""Tests for ML007 (mutable-default-argument), ML008 (too-many-arguments),
and ML009 (unused-import).

Follows the same pattern as the existing rule tests: parse a small source
snippet, run just that rule's `.check()`, and assert on the diagnostics it
returns.
"""

import ast

from minilint.rules.mutable_default_argument import MutableDefaultArgumentRule
from minilint.rules.too_many_arguments import TooManyArgumentsRule
from minilint.rules.unused_import import UnusedImportRule


def _check(rule_cls, source, **kwargs):
    tree = ast.parse(source)
    return rule_cls(**kwargs).check(tree)


# --- ML007: mutable-default-argument -----------------------------------


def test_list_default_is_flagged():
    diags = _check(MutableDefaultArgumentRule, "def f(x=[]):\n    pass\n")
    assert len(diags) == 1
    assert diags[0].rule_id == "ML007"
    assert "f" in diags[0].message


def test_dict_and_set_defaults_are_flagged():
    diags = _check(
        MutableDefaultArgumentRule, "def f(x={}, *, y=set()):\n    pass\n"
    )
    assert len(diags) == 2


def test_none_default_is_not_flagged():
    diags = _check(MutableDefaultArgumentRule, "def f(x=None):\n    pass\n")
    assert diags == []


def test_immutable_literal_default_is_not_flagged():
    diags = _check(
        MutableDefaultArgumentRule, "def f(x=1, y='a', z=(1, 2)):\n    pass\n"
    )
    assert diags == []


def test_non_empty_factory_call_is_not_flagged():
    # list(x) copies x rather than sharing a single fresh mutable object as
    # the *default value itself*; the risky pattern is specifically the
    # zero-argument factory call.
    diags = _check(MutableDefaultArgumentRule, "def f(x=list(range(3))):\n    pass\n")
    assert diags == []


# --- ML008: too-many-arguments -------------------------------------------


def test_function_under_limit_is_not_flagged():
    diags = _check(TooManyArgumentsRule, "def f(a, b, c):\n    pass\n")
    assert diags == []


def test_function_over_limit_is_flagged():
    diags = _check(TooManyArgumentsRule, "def f(a, b, c, d, e, f):\n    pass\n")
    assert len(diags) == 1
    assert diags[0].rule_id == "ML008"


def test_self_is_not_counted():
    src = "class C:\n    def m(self, a, b, c, d, e):\n        pass\n"
    diags = _check(TooManyArgumentsRule, src)
    assert diags == []  # 5 real params after excluding self == default max


def test_cls_is_not_counted():
    src = "class C:\n    @classmethod\n    def m(cls, a, b, c, d, e):\n        pass\n"
    diags = _check(TooManyArgumentsRule, src)
    assert diags == []


def test_threshold_is_configurable():
    diags = _check(TooManyArgumentsRule, "def f(a, b, c):\n    pass\n", max_args=2)
    assert len(diags) == 1


# --- ML009: unused-import -------------------------------------------------


def test_unused_plain_import_is_flagged():
    diags = _check(UnusedImportRule, "import os\n")
    assert len(diags) == 1
    assert "os" in diags[0].message


def test_used_import_is_not_flagged():
    diags = _check(UnusedImportRule, "import os\nos.getcwd()\n")
    assert diags == []


def test_used_via_attribute_access_is_not_flagged():
    diags = _check(UnusedImportRule, "import json\nprint(json.dumps({}))\n")
    assert diags == []


def test_unused_from_import_is_flagged():
    diags = _check(UnusedImportRule, "from collections import OrderedDict\n")
    assert len(diags) == 1
    assert "OrderedDict" in diags[0].message


def test_aliased_import_uses_the_alias_name():
    diags = _check(UnusedImportRule, "import numpy as np\n")
    assert len(diags) == 1
    assert "np" in diags[0].message
    assert "numpy" not in diags[0].message.split("'")[1]


def test_used_aliased_import_is_not_flagged():
    diags = _check(UnusedImportRule, "import numpy as np\nnp.array([1])\n")
    assert diags == []


def test_star_import_is_never_flagged():
    # We can't statically know what names a star-import binds, so we must
    # not guess -- flagging it would risk false positives on every name
    # used afterwards. This documents that as a deliberate non-goal.
    diags = _check(UnusedImportRule, "from os import *\n")
    assert diags == []


def test_dotted_import_binds_the_top_level_name():
    diags = _check(UnusedImportRule, "import os.path\n")
    assert len(diags) == 1
    assert diags[0].message.split("'")[1] == "os"


def test_reexport_via_dunder_all_is_not_flagged():
    src = "from mypkg import helper\n\n__all__ = ['helper']\n"
    diags = _check(UnusedImportRule, src)
    assert diags == []


def test_import_used_only_in_type_annotation_of_variable():
    # Real usage in an *unquoted* annotation is a normal Load and should
    # count.
    diags = _check(
        UnusedImportRule, "from typing import List\n\nx: List[int] = []\n"
    )
    assert diags == []
