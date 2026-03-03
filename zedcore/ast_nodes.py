"""AST node definitions for ZedCore / ZedSyntax."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Any


# ── Top-level ─────────────────────────────────────────────────────────────────

@dataclass
class Program:
    preamble: "Preamble"
    definitions: List["FunctionDef"]

    # Convenience: lookup a named (un)define
    def get_define(self, name: str) -> Optional["FunctionDef"]:
        for d in self.definitions:
            if d.name == name and not d.is_retro:
                return d
        return None

    def get_undefine(self, name: str) -> Optional["FunctionDef"]:
        for d in self.definitions:
            if d.name == name and d.is_retro:
                return d
        return None


@dataclass
class Preamble:
    """Parsed `syntax { … }` block."""

    rules: List[Any]  # list of rule nodes (InheritRule, TokenDef, etc.)

    @property
    def inherits(self) -> List[str]:
        return [r.name for r in self.rules if isinstance(r, InheritRule)]


@dataclass
class InheritRule:
    name: str  # e.g. "ZedSyntax"


@dataclass
class TokenDef:
    identifier: str
    pattern: str


@dataclass
class TransformDef:
    token_expr: str
    zed_expr: str


@dataclass
class PrecDef:
    identifier: str
    level: int


# ── Definitions ───────────────────────────────────────────────────────────────

@dataclass
class FunctionDef:
    name: str
    params: List[str]
    body: List[Any]  # list of statements
    is_retro: bool = False  # True for `undefine`


# ── Statements ────────────────────────────────────────────────────────────────

@dataclass
class Assignment:
    var: str
    expr: Any  # expression node


@dataclass
class Outward:
    expr: Any


@dataclass
class Inward:
    pass


@dataclass
class When:
    condition: Any
    then_body: List[Any]
    else_body: Optional[List[Any]] = None


@dataclass
class Cycle:
    var: str
    init_expr: Any
    condition: Any
    body: List[Any]


@dataclass
class Uncycle:
    body: List[Any]


@dataclass
class ReturnStmt:
    expr: Any


# ── Expressions ───────────────────────────────────────────────────────────────

@dataclass
class BinOp:
    op: str   # '+', '-', '*', '/', '%', '=', '!=', '<', '>', '<=', '>='
    left: Any
    right: Any


@dataclass
class Apply:
    """Forward application: func -> arg."""
    func: Any
    arg: Any


@dataclass
class RetroApply:
    """Retrograde application: func ⟵ arg."""
    func: Any
    arg: Any


@dataclass
class Compose:
    """Function composition: f ∘ g."""
    left: Any
    right: Any


@dataclass
class NullBind:
    """Null-binding operator: ∅x.M — binds x to z in M."""
    var: str
    body: Any


@dataclass
class Cons:
    """Sequence cons: left :: right."""
    left: Any
    right: Any


@dataclass
class FieldAccess:
    """obj.field."""
    obj: Any
    field: str


@dataclass
class MethodCall:
    """obj.method(args)."""
    obj: Any
    method: str
    args: List[Any]


@dataclass
class Identifier:
    name: str


@dataclass
class StringLit:
    value: str


@dataclass
class IntLit:
    value: int


@dataclass
class FloatLit:
    value: float


@dataclass
class CharLit:
    value: str  # single character


@dataclass
class ZeroTerm:
    """The `z` term — ground state of computation."""
    pass


@dataclass
class BoolLit:
    value: bool


@dataclass
class LambdaExpr:
    """Anonymous lambda: λx.body"""
    param: str
    body: Any


@dataclass
class BlockExpr:
    """Inline block expression returning a value."""
    stmts: List[Any]
