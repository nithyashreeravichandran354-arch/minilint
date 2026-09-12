"""Shared diagnostic data structure used by every rule."""

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Diagnostic:
    line: int
    col: int
    rule_id: str
    message: str

    def format(self, filename: str) -> str:
        return f"{filename}:{self.line}:{self.col}: [{self.rule_id}] {self.message}"
