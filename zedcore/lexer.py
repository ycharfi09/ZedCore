"""ZedSyntax lexer.

Tokenises a ZedCore source file under the ZedSyntax preamble (§6 of spec).
The lexer also handles the `syntax { … }` preamble block itself.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

# ── Token types ───────────────────────────────────────────────────────────────

# Keyword tokens
KW_SYNTAX    = "SYNTAX"
KW_INHERIT   = "INHERIT"
KW_TOKEN     = "TOKEN"
KW_MAP       = "MAP"
KW_PREC      = "PREC"
KW_DEFINE    = "DEFINE"
KW_UNDEFINE  = "UNDEFINE"
KW_WHEN      = "WHEN"
KW_OTHERWISE = "OTHERWISE"
KW_CYCLE     = "CYCLE"
KW_UNTIL     = "UNTIL"
KW_UNCYCLE   = "UNCYCLE"
KW_OUTWARD   = "OUTWARD"
KW_INWARD    = "INWARD"
KW_OUTWARD_RETRO = "OUTWARD_RETRO"   # retrograde outward (used internally)

# Literals
TK_STRING    = "STRING"
TK_FLOAT     = "FLOAT"
TK_INTEGER   = "INTEGER"
TK_CHAR      = "CHAR"
TK_ZERO      = "ZERO"
TK_TRUE      = "TRUE"
TK_FALSE     = "FALSE"

# Identifiers
TK_IDENT     = "IDENT"

# Operators / punctuation
TK_ASSIGN    = "ASSIGN"      # ← or :=
TK_FWD_APPLY = "FWD_APPLY"  # ->
TK_RET_APPLY = "RET_APPLY"  # ⟵ or <-
TK_COMPOSE   = "COMPOSE"    # ∘
TK_NULL_BIND = "NULL_BIND"  # ∅
TK_CONS      = "CONS"       # ::
TK_EQ        = "EQ"         # =
TK_NEQ       = "NEQ"        # !=
TK_LT        = "LT"         # <
TK_GT        = "GT"         # >
TK_LEQ       = "LEQ"        # <=
TK_GEQ       = "GEQ"        # >=
TK_PLUS      = "PLUS"       # +
TK_MINUS     = "MINUS"      # -
TK_STAR      = "STAR"       # *
TK_SLASH     = "SLASH"      # /
TK_PERCENT   = "PERCENT"    # %
TK_DOT       = "DOT"        # .
TK_COMMA     = "COMMA"      # ,
TK_SEMI      = "SEMI"       # ;
TK_COLON     = "COLON"      # :
TK_LPAREN    = "LPAREN"     # (
TK_RPAREN    = "RPAREN"     # )
TK_LBRACE    = "LBRACE"     # {
TK_RBRACE    = "RBRACE"     # }
TK_LBRACKET  = "LBRACKET"   # [
TK_RBRACKET  = "RBRACKET"   # ]

TK_EOF       = "EOF"
TK_NEWLINE   = "NEWLINE"


@dataclass
class Token:
    type: str
    value: str
    line: int
    col: int

    def __repr__(self) -> str:
        return f"Token({self.type}, {self.value!r}, {self.line}:{self.col})"


# ── Keyword map ───────────────────────────────────────────────────────────────

_KEYWORDS: dict[str, str] = {
    "syntax":    KW_SYNTAX,
    "inherit":   KW_INHERIT,
    "token":     KW_TOKEN,
    "map":       KW_MAP,
    "prec":      KW_PREC,
    "define":    KW_DEFINE,
    "undefine":  KW_UNDEFINE,
    "when":      KW_WHEN,
    "otherwise": KW_OTHERWISE,
    "cycle":     KW_CYCLE,
    "until":     KW_UNTIL,
    "uncycle":   KW_UNCYCLE,
    "outward":   KW_OUTWARD,
    "inward":    KW_INWARD,
    "z":         TK_ZERO,
    "true":      TK_TRUE,
    "false":     TK_FALSE,
}

# Characters that cannot appear in the middle of an identifier
_NOT_IDENT = set(" \t\r\n{}()[],.;:=!<>+*/%\"'`~@#^&|\\")


class Lexer:
    """ZedSyntax lexer.

    Identifiers may contain hyphens (e.g. `char-to-num`), as long as the
    hyphen is not at the start or end and is surrounded by word characters.
    """

    def __init__(self, source: str) -> None:
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self._tokens: List[Token] = []

    # ── Public API ────────────────────────────────────────────────────────────

    def tokenize(self) -> List[Token]:
        while self.pos < len(self.source):
            self._skip_whitespace_and_comments()
            if self.pos >= len(self.source):
                break
            tok = self._next_token()
            if tok is not None:
                self._tokens.append(tok)
        self._tokens.append(Token(TK_EOF, "", self.line, self.col))
        return self._tokens

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _peek(self, offset: int = 0) -> str:
        idx = self.pos + offset
        return self.source[idx] if idx < len(self.source) else ""

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _skip_whitespace_and_comments(self) -> None:
        while self.pos < len(self.source):
            ch = self._peek()
            if ch in " \t\r\n":
                self._advance()
            elif ch == "/" and self._peek(1) == "/":
                # Line comment
                while self.pos < len(self.source) and self._peek() != "\n":
                    self._advance()
            elif ch == "/" and self._peek(1) == "*":
                # Block comment
                self._advance()
                self._advance()
                while self.pos < len(self.source):
                    if self._peek() == "*" and self._peek(1) == "/":
                        self._advance()
                        self._advance()
                        break
                    self._advance()
            else:
                break

    def _tok(self, typ: str, val: str) -> Token:
        return Token(typ, val, self.line, self.col)

    def _next_token(self) -> Optional[Token]:  # noqa: C901
        start_line = self.line
        start_col = self.col
        ch = self._peek()

        def tok(typ: str, val: str) -> Token:
            return Token(typ, val, start_line, start_col)

        # ── Strings ───────────────────────────────────────────────────────────
        if ch == '"':
            return self._read_string(start_line, start_col)

        # ── Character literals ────────────────────────────────────────────────
        if ch == "'":
            return self._read_char(start_line, start_col)

        # ── Numbers ───────────────────────────────────────────────────────────
        if ch.isdigit():
            return self._read_number(start_line, start_col)

        # ── Unicode operators ─────────────────────────────────────────────────
        if ch == "←":
            self._advance()
            return tok(TK_ASSIGN, "←")
        if ch == "⟵":
            self._advance()
            return tok(TK_RET_APPLY, "⟵")
        if ch == "∘":
            self._advance()
            return tok(TK_COMPOSE, "∘")
        if ch == "∅":
            self._advance()
            return tok(TK_NULL_BIND, "∅")
        if ch == "Ƶ":
            # Ƶ-calculus references (in preamble map rules)
            return self._read_zed_ref(start_line, start_col)

        # ── Two-character operators ───────────────────────────────────────────
        two = ch + self._peek(1)
        if two == "->":
            self._advance(); self._advance()
            return tok(TK_FWD_APPLY, "->")
        if two == "<-":
            self._advance(); self._advance()
            return tok(TK_RET_APPLY, "<-")
        if two == ":=":
            self._advance(); self._advance()
            return tok(TK_ASSIGN, ":=")
        if two == "::":
            self._advance(); self._advance()
            return tok(TK_CONS, "::")
        if two == "!=":
            self._advance(); self._advance()
            return tok(TK_NEQ, "!=")
        if two == "<=":
            self._advance(); self._advance()
            return tok(TK_LEQ, "<=")
        if two == ">=":
            self._advance(); self._advance()
            return tok(TK_GEQ, ">=")

        # ── Single-character operators ────────────────────────────────────────
        single_map = {
            "=": TK_EQ,
            "<": TK_LT,
            ">": TK_GT,
            "+": TK_PLUS,
            "-": TK_MINUS,
            "*": TK_STAR,
            "/": TK_SLASH,
            "%": TK_PERCENT,
            ".": TK_DOT,
            ",": TK_COMMA,
            ";": TK_SEMI,
            ":": TK_COLON,
            "(": TK_LPAREN,
            ")": TK_RPAREN,
            "{": TK_LBRACE,
            "}": TK_RBRACE,
            "[": TK_LBRACKET,
            "]": TK_RBRACKET,
        }
        if ch in single_map:
            self._advance()
            return tok(single_map[ch], ch)

        # ── Identifiers and keywords ──────────────────────────────────────────
        if ch.isalpha() or ch == "_":
            return self._read_ident(start_line, start_col)

        # Unknown character — skip with a warning
        self._advance()
        return None

    def _read_string(self, line: int, col: int) -> Token:
        self._advance()  # opening "
        buf = []
        while self.pos < len(self.source):
            ch = self._peek()
            if ch == '"':
                self._advance()
                break
            if ch == "\\":
                self._advance()
                esc = self._advance()
                buf.append({"n": "\n", "t": "\t", "r": "\r", '"': '"',
                             "\\": "\\"}.get(esc, esc))
            else:
                buf.append(self._advance())
        return Token(TK_STRING, "".join(buf), line, col)

    def _read_char(self, line: int, col: int) -> Token:
        self._advance()  # opening '
        ch = self._advance()
        if ch == "\\" and self.pos < len(self.source):
            esc = self._advance()
            ch = {"n": "\n", "t": "\t", "r": "\r", "'": "'",
                  "\\": "\\"}.get(esc, esc)
        if self.pos < len(self.source) and self._peek() == "'":
            self._advance()  # closing '
        return Token(TK_CHAR, ch, line, col)

    def _read_number(self, line: int, col: int) -> Token:
        buf = []
        while self.pos < len(self.source) and self._peek().isdigit():
            buf.append(self._advance())
        if self.pos < len(self.source) and self._peek() == "." and \
                self.pos + 1 < len(self.source) and self._peek(1).isdigit():
            buf.append(self._advance())  # '.'
            while self.pos < len(self.source) and self._peek().isdigit():
                buf.append(self._advance())
            return Token(TK_FLOAT, "".join(buf), line, col)
        return Token(TK_INTEGER, "".join(buf), line, col)

    def _read_ident(self, line: int, col: int) -> Token:
        buf = []
        while self.pos < len(self.source):
            ch = self._peek()
            # Allow hyphenated identifiers (e.g. char-to-num)
            # A hyphen is part of the ident if the next char is alphanumeric/_
            if ch.isalnum() or ch == "_":
                buf.append(self._advance())
            elif ch == "-" and self.pos + 1 < len(self.source) and \
                    (self._peek(1).isalnum() or self._peek(1) == "_"):
                buf.append(self._advance())
            else:
                break
        word = "".join(buf)
        typ = _KEYWORDS.get(word, TK_IDENT)
        return Token(typ, word, line, col)

    def _read_zed_ref(self, line: int, col: int) -> Token:
        """Read a Ƶ.something reference used in preamble map rules."""
        buf = [self._advance()]  # Ƶ
        if self.pos < len(self.source) and self._peek() == ".":
            buf.append(self._advance())
            while self.pos < len(self.source):
                ch = self._peek()
                if ch.isalnum() or ch in "._-":
                    buf.append(self._advance())
                else:
                    break
        return Token(TK_IDENT, "".join(buf), line, col)
