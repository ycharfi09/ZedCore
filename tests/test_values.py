"""Tests for the ZedCore values module."""

import pytest
from zedcore.values import (
    Z, _ZeroTermClass, ZedList, ZedFunction, ZedBuiltin,
    zed_truthy, zed_repr, zed_add, zed_sub, zed_mul, zed_div, zed_mod,
    zed_compare, zed_eq,
)


# ── Zero term ─────────────────────────────────────────────────────────────────

class TestZeroTerm:
    def test_z_is_singleton(self):
        from zedcore.values import _ZeroTermClass
        assert _ZeroTermClass() is Z

    def test_z_repr(self):
        assert repr(Z) == "z"
        assert str(Z) == "z"

    def test_z_falsy(self):
        assert not bool(Z)
        assert not zed_truthy(Z)

    def test_z_equals_z(self):
        assert Z == Z
        assert zed_eq(Z, Z)

    def test_z_equals_empty_list(self):
        empty = ZedList.empty()
        assert zed_eq(Z, empty)
        assert zed_eq(empty, Z)


# ── ZedList ───────────────────────────────────────────────────────────────────

class TestZedList:
    def test_empty_list(self):
        lst = ZedList.empty()
        assert lst.is_empty

    def test_from_py_list(self):
        lst = ZedList.from_py_list([1, 2, 3])
        assert not lst.is_empty
        assert lst.head == 1

    def test_from_py_list_empty(self):
        result = ZedList.from_py_list([])
        assert result is Z

    def test_from_string(self):
        lst = ZedList.from_string("abc")
        py = lst.to_py_list()
        assert py == ["a", "b", "c"]

    def test_to_py_list(self):
        lst = ZedList.from_py_list([1, 2, 3])
        assert lst.to_py_list() == [1, 2, 3]

    def test_length(self):
        lst = ZedList.from_py_list([1, 2, 3])
        assert len(lst) == 3

    def test_str_chars(self):
        lst = ZedList.from_string("hello")
        assert str(lst) == "hello"

    def test_equality(self):
        a = ZedList.from_py_list([1, 2])
        b = ZedList.from_py_list([1, 2])
        c = ZedList.from_py_list([1, 3])
        assert a == b
        assert a != c

    def test_truthy(self):
        lst = ZedList.from_py_list([1])
        assert zed_truthy(lst)
        assert not zed_truthy(ZedList.empty())


# ── Arithmetic ────────────────────────────────────────────────────────────────

class TestArithmetic:
    def test_add_ints(self):
        assert zed_add(3, 4) == 7

    def test_sub_ints(self):
        assert zed_sub(10, 3) == 7

    def test_mul_ints(self):
        assert zed_mul(3, 4) == 12

    def test_div_ints(self):
        assert zed_div(10, 2) == 5

    def test_mod_ints(self):
        assert zed_mod(10, 3) == 1

    def test_add_strings(self):
        assert zed_add("hello", " world") == "hello world"

    def test_z_add(self):
        assert zed_add(Z, 5) == 5
        assert zed_add(5, Z) == 5

    def test_char_sub_char(self):
        # 'B' - 'A' = 1
        assert zed_sub("B", "A") == 1

    def test_char_sub_int(self):
        # 'B' - 1 = 'A'
        assert zed_sub("B", 1) == "A"

    def test_char_add_int(self):
        assert zed_add("A", 1) == "B"


# ── Comparisons ───────────────────────────────────────────────────────────────

class TestComparisons:
    def test_eq(self):
        assert zed_compare("=", 1, 1)
        assert not zed_compare("=", 1, 2)

    def test_neq(self):
        assert zed_compare("!=", 1, 2)
        assert not zed_compare("!=", 1, 1)

    def test_lt(self):
        assert zed_compare("<", 1, 2)
        assert not zed_compare("<", 2, 1)

    def test_gt(self):
        assert zed_compare(">", 2, 1)

    def test_leq(self):
        assert zed_compare("<=", 1, 1)
        assert zed_compare("<=", 1, 2)

    def test_geq(self):
        assert zed_compare(">=", 2, 2)
        assert zed_compare(">=", 3, 2)

    def test_char_comparison(self):
        assert zed_compare(">=", "B", "A")
        assert not zed_compare(">=", "A", "B")


# ── zed_repr ──────────────────────────────────────────────────────────────────

class TestZedRepr:
    def test_z_repr(self):
        assert zed_repr(Z) == "z"

    def test_int_repr(self):
        assert zed_repr(42) == "42"

    def test_string_repr(self):
        assert zed_repr("hello") == "hello"

    def test_bool_repr(self):
        assert zed_repr(True) == "true"
        assert zed_repr(False) == "false"
