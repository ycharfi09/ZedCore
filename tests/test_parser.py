"""Tests for the ZedCore parser."""

import pytest
from zedcore.lexer import Lexer
from zedcore.parser import Parser
from zedcore.ast_nodes import (
    Program, Preamble, InheritRule, FunctionDef,
    Outward, Inward, Assignment, When, Cycle,
    Apply, BinOp, StringLit, IntLit, ZeroTerm, Identifier,
    Cons,
)


def parse(source: str) -> Program:
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


# ── Preamble ──────────────────────────────────────────────────────────────────

class TestPreamble:
    def test_null_preamble(self):
        prog = parse("define main { outward z }")
        assert prog.preamble.rules == []

    def test_inherit_zedsyntax(self):
        prog = parse('syntax { inherit ZedSyntax; }\ndefine main { outward z }')
        assert len(prog.preamble.rules) == 1
        assert isinstance(prog.preamble.rules[0], InheritRule)
        assert prog.preamble.rules[0].name == "ZedSyntax"

    def test_multiple_rules(self):
        src = """
        syntax {
          inherit ZedSyntax;
          inherit ZedCore.bootstrap;
        }
        define main { outward z }
        """
        prog = parse(src)
        assert len(prog.preamble.rules) == 2


# ── Function definitions ──────────────────────────────────────────────────────

class TestFunctionDefs:
    def test_simple_define(self):
        prog = parse("define main { outward z }")
        assert len(prog.definitions) == 1
        d = prog.definitions[0]
        assert isinstance(d, FunctionDef)
        assert d.name == "main"
        assert d.params == []
        assert not d.is_retro

    def test_define_with_params(self):
        prog = parse("define add (a, b) { outward a }")
        d = prog.definitions[0]
        assert d.params == ["a", "b"]

    def test_undefine(self):
        prog = parse("undefine main { outward z }")
        d = prog.definitions[0]
        assert d.is_retro

    def test_hyphenated_name(self):
        prog = parse("define char-to-num (c) { outward c }")
        d = prog.definitions[0]
        assert d.name == "char-to-num"

    def test_define_and_undefine(self):
        src = """
        define greet { outward "hi" }
        undefine greet { outward "bye" }
        """
        prog = parse(src)
        assert len(prog.definitions) == 2
        assert prog.definitions[0].name == "greet"
        assert not prog.definitions[0].is_retro
        assert prog.definitions[1].name == "greet"
        assert prog.definitions[1].is_retro


# ── Statements ────────────────────────────────────────────────────────────────

class TestStatements:
    def test_outward_string(self):
        prog = parse('define main { outward "hello" }')
        stmt = prog.definitions[0].body[0]
        assert isinstance(stmt, Outward)
        assert isinstance(stmt.expr, StringLit)
        assert stmt.expr.value == "hello"

    def test_outward_zero(self):
        prog = parse("define main { outward z }")
        stmt = prog.definitions[0].body[0]
        assert isinstance(stmt, Outward)
        assert isinstance(stmt.expr, ZeroTerm)

    def test_assignment(self):
        prog = parse("define main { x ← 42 }")
        stmt = prog.definitions[0].body[0]
        assert isinstance(stmt, Assignment)
        assert stmt.var == "x"
        assert isinstance(stmt.expr, IntLit)
        assert stmt.expr.value == 42

    def test_inward_assignment(self):
        prog = parse("define main { x ← inward }")
        stmt = prog.definitions[0].body[0]
        assert isinstance(stmt, Assignment)
        assert isinstance(stmt.expr, Inward)

    def test_when_no_else(self):
        prog = parse("define main { when x { outward 1 } }")
        stmt = prog.definitions[0].body[0]
        assert isinstance(stmt, When)
        assert stmt.else_body is None

    def test_when_with_else(self):
        prog = parse("""
        define main {
          when x { outward 1 } otherwise { outward 0 }
        }
        """)
        stmt = prog.definitions[0].body[0]
        assert isinstance(stmt, When)
        assert stmt.else_body is not None

    def test_cycle(self):
        prog = parse("""
        define main {
          cycle i ← 0 until i > 10 {
            outward i
          }
        }
        """)
        stmt = prog.definitions[0].body[0]
        assert isinstance(stmt, Cycle)
        assert stmt.var == "i"


# ── Expressions ───────────────────────────────────────────────────────────────

class TestExpressions:
    def test_apply(self):
        prog = parse("define main { outward f -> x }")
        outward = prog.definitions[0].body[0]
        assert isinstance(outward.expr, Apply)

    def test_chained_apply(self):
        prog = parse("define main { outward map -> f -> seq }")
        outward = prog.definitions[0].body[0]
        # Should be left-associative: (map -> f) -> seq
        assert isinstance(outward.expr, Apply)
        assert isinstance(outward.expr.func, Apply)

    def test_binop_add(self):
        prog = parse("define main { outward 1 + 2 }")
        stmt = prog.definitions[0].body[0]
        assert isinstance(stmt.expr, BinOp)
        assert stmt.expr.op == "+"

    def test_cons(self):
        prog = parse("define main { outward 1 :: 2 :: z }")
        stmt = prog.definitions[0].body[0]
        assert isinstance(stmt.expr, Cons)

    def test_comparison(self):
        prog = parse("define main { when x = z { outward 1 } }")
        stmt = prog.definitions[0].body[0]
        assert isinstance(stmt.condition, BinOp)
        assert stmt.condition.op == "="
