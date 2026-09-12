
from .bare_except import BareExceptRule
from .none_comparison import NoneComparisonRule
from .dead_code import DeadCodeRule
from .unused_variable import UnusedVariableRule
from .shadowed_variable import ShadowedVariableRule
from .use_before_assignment import UseBeforeAssignmentRule
from .mutable_default_argument import MutableDefaultArgumentRule
from .too_many_arguments import TooManyArgumentsRule
from .unused_import import UnusedImportRule

ALL_RULES = [
    BareExceptRule,
    NoneComparisonRule,
    DeadCodeRule,
    UnusedVariableRule,
    ShadowedVariableRule,
    UseBeforeAssignmentRule,
    MutableDefaultArgumentRule,
    TooManyArgumentsRule,
    UnusedImportRule,
]

__all__ = ["ALL_RULES"] + [cls.__name__ for cls in ALL_RULES]
