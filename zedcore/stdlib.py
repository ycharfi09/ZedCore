"""ZedCore standard library (zedstd).

Provides built-in functions and the string/sequence operations used by
ZedSyntax programs.  These are registered into the root environment before
any user program runs.

§10 of the spec describes the standard library sketch.
"""

from __future__ import annotations

from typing import Any, List

from .values import (
    Z, _ZeroTermClass, ZedList, ZedBuiltin, ZedPartial,
    zed_truthy, zed_repr,
)
from .errors import ZedRuntimeError


# ── String / sequence helpers ─────────────────────────────────────────────────

def _to_zedlist(val: Any) -> Any:
    """Convert a Python string or existing ZedList to a ZedList of chars."""
    if isinstance(val, str):
        return ZedList.from_string(val)
    if isinstance(val, ZedList):
        return val
    if val is Z:
        return Z
    return ZedList.from_py_list([val])


def _to_str(val: Any) -> str:
    """Coerce a ZedCore value to a Python string."""
    if val is Z:
        return "z"
    if isinstance(val, ZedList):
        return str(val)
    return str(val)


# ── String method dispatcher ─────────────────────────────────────────────────

def string_method(obj: Any, method: str, args: List[Any]) -> Any:
    """Dispatch built-in string / sequence methods."""
    s = _to_str(obj) if not isinstance(obj, ZedList) else None
    lst = obj if isinstance(obj, ZedList) else None

    # .length
    if method == "length":
        if s is not None and not isinstance(obj, ZedList):
            return len(s)
        if lst is not None:
            return len(lst.to_py_list())
        return 0

    # .slice(start) or .slice(start, end)
    if method == "slice":
        target = s if s is not None and not isinstance(obj, ZedList) else None
        if target is None and lst is not None:
            items = lst.to_py_list()
            target_list = items
            if len(args) == 1:
                start = args[0] if args[0] is not Z else 0
                sliced = target_list[int(start):]
            elif len(args) == 2:
                a = args[0] if args[0] is not Z else 0
                b = args[1] if args[1] is not Z else len(target_list)
                sliced = target_list[int(a):int(b)]
            else:
                sliced = target_list
            return ZedList.from_py_list(sliced)
        if target is not None:
            if len(args) == 1:
                start = args[0] if args[0] is not Z else 0
                return target[int(start):]
            elif len(args) == 2:
                a = args[0] if args[0] is not Z else 0
                b = args[1] if args[1] is not Z else len(target)
                return target[int(a):int(b)]
        return obj

    # .first / .head
    if method in ("first", "head"):
        if isinstance(obj, ZedList) and not obj.is_empty:
            return obj.head
        if isinstance(obj, str) and obj:
            return obj[0]
        return Z

    # .rest / .tail
    if method in ("rest", "tail"):
        if isinstance(obj, ZedList) and not obj.is_empty:
            return obj.tail
        if isinstance(obj, str) and len(obj) > 1:
            return obj[1:]
        return Z

    # .empty
    if method == "empty":
        if isinstance(obj, ZedList):
            return obj.is_empty
        if obj is Z:
            return True
        if isinstance(obj, str):
            return len(obj) == 0
        return False

    # .chunks(n)
    if method == "chunks":
        n = int(args[0]) if args and args[0] is not Z else 1
        items = _to_str(obj) if not isinstance(obj, ZedList) else None
        if items is not None:
            chunks = [items[i:i+n] for i in range(0, len(items), n)]
            return ZedList.from_py_list(chunks)
        if isinstance(obj, ZedList):
            py = obj.to_py_list()
            chunks_list = [
                ZedList.from_py_list(py[i:i+n])
                for i in range(0, len(py), n)
            ]
            return ZedList.from_py_list(chunks_list)
        return Z

    # .as-integer / .as_integer
    if method in ("as-integer", "as_integer"):
        try:
            return int(_to_str(obj))
        except (ValueError, TypeError):
            return Z

    # .to-upper / .to_upper
    if method in ("to-upper", "to_upper", "upper"):
        return _to_str(obj).upper()

    # .to-lower / .to_lower
    if method in ("to-lower", "to_lower", "lower"):
        return _to_str(obj).lower()

    # .strip-spaces / .strip
    if method in ("strip-spaces", "strip_spaces", "strip"):
        return _to_str(obj).replace(" ", "")

    # .replace
    if method == "replace":
        if len(args) >= 2:
            return _to_str(obj).replace(_to_str(args[0]), _to_str(args[1]))
        return obj

    # .split
    if method == "split":
        sep = _to_str(args[0]) if args else None
        parts = _to_str(obj).split(sep)
        return ZedList.from_py_list(parts)

    raise ZedRuntimeError(f"Unknown method .{method} on {obj!r}")


# ── Built-in functions ─────────────────────────────────────────────────────

def _builtin_print(val: Any) -> Any:
    """Not a direct std function; used internally."""
    print(zed_repr(val))
    return Z


def _make_builtins() -> dict:
    """Return the standard built-in function table."""

    def _map(f: Any) -> Any:
        """map f → a function expecting a sequence."""
        def _map_seq(seq: Any) -> Any:
            from .interpreter import _apply_value
            if seq is Z or (isinstance(seq, ZedList) and seq.is_empty):
                return Z
            if isinstance(seq, ZedList):
                items = seq.to_py_list()
                result = [_apply_value(f, [item]) for item in items]
                return ZedList.from_py_list(result)
            if isinstance(seq, str):
                result = [_apply_value(f, [c]) for c in seq]
                return ZedList.from_py_list(result)
            return Z
        return ZedBuiltin(name="map/seq", func=_map_seq)

    def _filter(f: Any) -> Any:
        def _filter_seq(seq: Any) -> Any:
            from .interpreter import _apply_value
            if seq is Z:
                return Z
            if isinstance(seq, ZedList):
                items = seq.to_py_list()
                result = [item for item in items
                          if zed_truthy(_apply_value(f, [item]))]
                return ZedList.from_py_list(result)
            return Z
        return ZedBuiltin(name="filter/seq", func=_filter_seq)

    def _fold(f: Any) -> Any:
        def _fold_init(init: Any) -> Any:
            def _fold_seq(seq: Any) -> Any:
                from .interpreter import _apply_value
                acc = init
                if isinstance(seq, ZedList):
                    for item in seq.to_py_list():
                        acc = _apply_value(_apply_value(f, [acc]), [item])
                return acc
            return ZedBuiltin(name="fold/seq", func=_fold_seq)
        return ZedBuiltin(name="fold/init", func=_fold_init)

    builtins = {
        "map":    ZedBuiltin("map",    _map),
        "filter": ZedBuiltin("filter", _filter),
        "fold":   ZedBuiltin("fold",   _fold),
        "not": ZedBuiltin("not", lambda v: not zed_truthy(v)),
        "and": ZedBuiltin("and", lambda a: ZedBuiltin("and/b",
                           lambda b: zed_truthy(a) and zed_truthy(b))),
        "or":  ZedBuiltin("or",  lambda a: ZedBuiltin("or/b",
                           lambda b: zed_truthy(a) or zed_truthy(b))),
        "int":    ZedBuiltin("int",  lambda v: int(v) if v is not Z else 0),
        "str":    ZedBuiltin("str",  lambda v: _to_str(v)),
        "len":    ZedBuiltin("len",  lambda v: len(_to_str(v))
                             if not isinstance(v, ZedList) else len(v.to_py_list())),
        "abs":    ZedBuiltin("abs",  lambda v: abs(v) if isinstance(v, (int, float)) else Z),
        "min":    ZedBuiltin("min",  lambda a: ZedBuiltin("min/b", lambda b: a if a < b else b)),
        "max":    ZedBuiltin("max",  lambda a: ZedBuiltin("max/b", lambda b: a if a > b else b)),
        # z is also available as the zero term constant
        "z":      Z,
    }
    return builtins


BUILTINS = _make_builtins()
