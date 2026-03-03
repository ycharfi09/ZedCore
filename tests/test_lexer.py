"""Tests for the ZedCore lexer."""

import pytest
from zedcore.lexer import Lexer, Token, TK_EOF, TK_IDENT, TK_INTEGER, TK_STRING, TK_ZERO
from zedcore.lexer import (
    KW_DEFINE, KW_UNDEFINE, KW_WHEN, KW_OTHERWISE, KW_OUTWARD, KW_INWARD,
    KW_SYNTAX, KW_INHERIT, TK_ASSIGN, TK_FWD_APPLY, TK_RET_APPLY,
    TK_LBRACE, TK_RBRACE, TK_CONS, TK_FLOAT, TK_CHAR,
)


def tokenize(source: str) -> list[Token]:
    return Lexer(source).tokenize()


def types(source: str) -> list[str]:
    return [t.type for t in tokenize(source) if t.type != TK_EOF]


# ── Keywords ──────────────────────────────────────────────────────────────────

class TestKeywords:
    def test_define(self):
        assert types("define") == [KW_DEFINE]

    def test_undefine(self):
        assert types("undefine") == [KW_UNDEFINE]

    def test_when_otherwise(self):
        assert types("when otherwise") == [KW_WHEN, KW_OTHERWISE]

    def test_outward_inward(self):
        assert types("outward inward") == [KW_OUTWARD, KW_INWARD]

    def test_syntax_inherit(self):
        assert types("syntax inherit") == [KW_SYNTAX, KW_INHERIT]

    def test_zero(self):
        assert types("z") == [TK_ZERO]


# ── Literals ──────────────────────────────────────────────────────────────────

class TestLiterals:
    def test_integer(self):
        toks = tokenize("42")
        assert toks[0].type == TK_INTEGER
        assert toks[0].value == "42"

    def test_float(self):
        toks = tokenize("3.14")
        assert toks[0].type == TK_FLOAT
        assert toks[0].value == "3.14"

    def test_string(self):
        toks = tokenize('"hello"')
        assert toks[0].type == TK_STRING
        assert toks[0].value == "hello"

    def test_string_escape(self):
        toks = tokenize(r'"hello\nworld"')
        assert toks[0].value == "hello\nworld"

    def test_char(self):
        toks = tokenize("'A'")
        assert toks[0].type == TK_CHAR
        assert toks[0].value == "A"


# ── Operators ─────────────────────────────────────────────────────────────────

class TestOperators:
    def test_unicode_assign(self):
        assert types("←") == [TK_ASSIGN]

    def test_ascii_assign(self):
        assert types(":=") == [TK_ASSIGN]

    def test_fwd_apply(self):
        assert types("->") == [TK_FWD_APPLY]

    def test_ret_apply_unicode(self):
        assert types("⟵") == [TK_RET_APPLY]

    def test_ret_apply_ascii(self):
        assert types("<-") == [TK_RET_APPLY]

    def test_cons(self):
        assert types("::") == [TK_CONS]


# ── Identifiers ───────────────────────────────────────────────────────────────

class TestIdentifiers:
    def test_simple(self):
        toks = tokenize("myVar")
        assert toks[0].type == TK_IDENT
        assert toks[0].value == "myVar"

    def test_hyphenated(self):
        toks = tokenize("char-to-num")
        assert toks[0].type == TK_IDENT
        assert toks[0].value == "char-to-num"

    def test_with_numbers(self):
        toks = tokenize("var123")
        assert toks[0].type == TK_IDENT
        assert toks[0].value == "var123"


# ── Comments ──────────────────────────────────────────────────────────────────

class TestComments:
    def test_line_comment(self):
        src = "// this is a comment\ndefine"
        assert types(src) == [KW_DEFINE]

    def test_inline_comment(self):
        src = "define // comment"
        assert types(src) == [KW_DEFINE]

    def test_block_comment(self):
        src = "/* block comment */ define"
        assert types(src) == [KW_DEFINE]


# ── Full preamble ─────────────────────────────────────────────────────────────

class TestPreamble:
    def test_simple_syntax_block(self):
        src = "syntax { inherit ZedSyntax; }"
        toks = tokenize(src)
        type_list = [t.type for t in toks if t.type != TK_EOF]
        assert KW_SYNTAX in type_list
        assert KW_INHERIT in type_list
