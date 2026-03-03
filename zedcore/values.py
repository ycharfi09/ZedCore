"""ZedCore runtime value types.

The ZedCore value universe (per the ZedCalculus and ZedSyntax spec):

  z            — ZeroTerm:  the only term defined outside any syntax context
  integers     — Python int (approximations of z per Principle V)
  floats       — Python float
  strings      — Python str
  characters   — single-char Python str (used when iterating strings)
  booleans     — Python bool  (TRUE / FALSE from ZedCalculus encoding)
  ZedList      — linked cons-list  (head :: tail, supports :: operator)
  ZedFunction  — a closure (params + body + captured environment)
  ZedBuiltin   — a built-in function implemented in Python
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .ast_nodes import FunctionDef


# ── Sentinel zero term ────────────────────────────────────────────────────────

class _ZeroTermClass:
    """Singleton representing the `z` term."""

    _instance: Optional["_ZeroTermClass"] = None

    def __new__(cls) -> "_ZeroTermClass":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "z"

    def __str__(self) -> str:
        return "z"

    def __bool__(self) -> bool:
        return False

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _ZeroTermClass)

    def __hash__(self) -> int:
        return hash("z")


Z = _ZeroTermClass()  # The one true z


# ── ZedList ───────────────────────────────────────────────────────────────────

@dataclass
class ZedList:
    """Cons-list. An empty list is represented by head=Z, tail=Z."""

    head: Any
    tail: Any  # ZedList or Z

    # ── Sequence protocol ─────────────────────────────────────────────────────

    @property
    def is_empty(self) -> bool:
        return self.head is Z and self.tail is Z

    @classmethod
    def empty(cls) -> "ZedList":
        return cls(head=Z, tail=Z)

    @classmethod
    def from_py_list(cls, items: list) -> Any:
        if not items:
            return Z
        result: Any = Z
        for item in reversed(items):
            result = cls(head=item, tail=result)
        return result

    @classmethod
    def from_string(cls, s: str) -> Any:
        """Turn a Python string into a ZedList of characters."""
        return cls.from_py_list(list(s))

    def to_py_list(self) -> list:
        items = []
        node: Any = self
        while isinstance(node, ZedList) and not node.is_empty:
            items.append(node.head)
            node = node.tail
        return items

    def to_string(self) -> str:
        """Reconstruct a Python string from a ZedList of chars."""
        return "".join(str(c) for c in self.to_py_list())

    def __len__(self) -> int:
        return len(self.to_py_list())

    def __repr__(self) -> str:
        items = self.to_py_list()
        return f"ZedList({items!r})"

    def __str__(self) -> str:
        items = self.to_py_list()
        # If all items are single chars, display as a string
        if all(isinstance(i, str) and len(i) == 1 for i in items):
            return "".join(items)
        return "[" + " :: ".join(str(i) for i in items) + "]"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, _ZeroTermClass):
            return self.is_empty
        if not isinstance(other, ZedList):
            return False
        a: Any = self
        b: Any = other
        while True:
            a_empty = isinstance(a, _ZeroTermClass) or \
                      (isinstance(a, ZedList) and a.is_empty)
            b_empty = isinstance(b, _ZeroTermClass) or \
                      (isinstance(b, ZedList) and b.is_empty)
            if a_empty and b_empty:
                return True
            if a_empty or b_empty:
                return False
            if not isinstance(a, ZedList) or not isinstance(b, ZedList):
                return a == b
            if a.head != b.head:
                return False
            a = a.tail
            b = b.tail

    def __hash__(self) -> int:
        return hash(tuple(self.to_py_list()))


# ── ZedFunction ───────────────────────────────────────────────────────────────

@dataclass
class ZedFunction:
    """A user-defined function (closure)."""

    name: str
    params: List[str]
    body: List[Any]       # list of AST statement nodes
    env: Any              # captured Environment (forward reference)
    is_retro: bool = False
    # Corresponding retro/forward definition (linked during runtime setup)
    paired: Optional["ZedFunction"] = field(default=None, repr=False,
                                            compare=False)

    def __repr__(self) -> str:
        direction = "undefine" if self.is_retro else "define"
        return f"<ZedFunction {direction} {self.name}({', '.join(self.params)})>"


# ── ZedBuiltin ────────────────────────────────────────────────────────────────

@dataclass
class ZedBuiltin:
    """A built-in function implemented in Python."""

    name: str
    func: Callable[..., Any]

    def __repr__(self) -> str:
        return f"<ZedBuiltin {self.name}>"


# ── ZedPartial ────────────────────────────────────────────────────────────────

@dataclass
class ZedPartial:
    """A partially-applied function (waiting for more arguments)."""

    func: Any  # ZedFunction | ZedBuiltin | ZedPartial
    applied: List[Any]  # arguments already supplied

    def __repr__(self) -> str:
        return f"<ZedPartial {self.func!r} {self.applied!r}>"


# ── Helpers ───────────────────────────────────────────────────────────────────

def zed_truthy(val: Any) -> bool:
    """ZedCore truth: z is falsy; everything else is truthy."""
    if val is Z:
        return False
    if isinstance(val, _ZeroTermClass):
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, int):
        return val != 0
    if isinstance(val, float):
        return val != 0.0
    if isinstance(val, str):
        return len(val) > 0
    if isinstance(val, ZedList):
        return not val.is_empty
    return True


def zed_repr(val: Any) -> str:
    """Human-readable representation of a ZedCore value."""
    if val is Z:
        return "z"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, ZedList):
        return str(val)
    return str(val)


def zed_eq(a: Any, b: Any) -> bool:
    """ZedCore equality."""
    if a is Z and b is Z:
        return True
    if isinstance(a, _ZeroTermClass) and isinstance(b, _ZeroTermClass):
        return True
    if isinstance(a, _ZeroTermClass) or isinstance(b, _ZeroTermClass):
        # z equals empty list
        a_empty = isinstance(a, ZedList) and a.is_empty
        b_empty = isinstance(b, ZedList) and b.is_empty
        if isinstance(a, _ZeroTermClass) and b_empty:
            return True
        if isinstance(b, _ZeroTermClass) and a_empty:
            return True
        return False
    if isinstance(a, ZedList) and isinstance(b, ZedList):
        return a == b
    return a == b


def char_to_int(c: Any) -> int:
    """Convert a character to its ordinal value (for char arithmetic)."""
    if isinstance(c, int):
        return c
    if isinstance(c, str) and len(c) == 1:
        return ord(c)
    raise TypeError(f"Cannot convert {c!r} to integer character code")


def int_to_char(n: int) -> str:
    """Convert an ordinal value to a character."""
    return chr(n)


def zed_add(a: Any, b: Any) -> Any:
    """ZedCore + operator."""
    # char + int → char
    if isinstance(a, str) and len(a) == 1 and isinstance(b, int):
        return chr(ord(a) + b)
    if isinstance(a, int) and isinstance(b, str) and len(b) == 1:
        return chr(ord(b) + a)
    # string concatenation
    if isinstance(a, str) and isinstance(b, str):
        return a + b
    # numeric
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        result = a + b
        if isinstance(a, int) and isinstance(b, int):
            return int(result)
        return result
    # z acts as 0
    if a is Z:
        return b
    if b is Z:
        return a
    return str(a) + str(b)


def zed_sub(a: Any, b: Any) -> Any:
    """ZedCore - operator."""
    # char - char → int
    if isinstance(a, str) and len(a) == 1 and isinstance(b, str) and len(b) == 1:
        return ord(a) - ord(b)
    # char - int → char
    if isinstance(a, str) and len(a) == 1 and isinstance(b, int):
        return chr(ord(a) - b)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        result = a - b
        if isinstance(a, int) and isinstance(b, int):
            return int(result)
        return result
    if a is Z:
        if isinstance(b, (int, float)):
            return -b
        return Z
    if b is Z:
        return a
    return Z


def zed_mul(a: Any, b: Any) -> Any:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        result = a * b
        if isinstance(a, int) and isinstance(b, int):
            return int(result)
        return result
    if a is Z or b is Z:
        return Z
    return Z


def zed_div(a: Any, b: Any) -> Any:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if b == 0:
            return Z
        if isinstance(a, int) and isinstance(b, int):
            return a // b
        return a / b
    return Z


def zed_mod(a: Any, b: Any) -> Any:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if b == 0:
            return Z
        return a % b
    return Z


def zed_compare(op: str, a: Any, b: Any) -> bool:
    """ZedCore comparison operators."""
    # z comparisons
    if a is Z and b is Z:
        return op in ("=", "<=", ">=")
    if a is Z:
        return op in ("<", "<=", "!=")
    if b is Z:
        return op in (">", ">=", "!=")
    # char comparisons (single-char strings)
    if isinstance(a, str) and len(a) == 1 and isinstance(b, str) and len(b) == 1:
        a_val: Any = a
        b_val: Any = b
    elif isinstance(a, str) and len(a) == 1 and isinstance(b, int):
        a_val = ord(a)
        b_val = b
    elif isinstance(a, int) and isinstance(b, str) and len(b) == 1:
        a_val = a
        b_val = ord(b)
    else:
        a_val = a
        b_val = b

    try:
        if op == "=":
            return zed_eq(a, b)
        if op == "!=":
            return not zed_eq(a, b)
        if op == "<":
            return a_val < b_val
        if op == ">":
            return a_val > b_val
        if op == "<=":
            return a_val <= b_val
        if op == ">=":
            return a_val >= b_val
    except TypeError:
        pass
    return False
