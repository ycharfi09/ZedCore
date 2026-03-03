"""ZedSyntax recursive-descent parser.

Parses a token stream produced by the lexer into an AST (see ast_nodes.py).

Operator precedence (higher number = tighter binding):
  5   ∅ (null-bind)
  10  ← (assignment)  — handled as a statement, not an expression
  15  :: (cons)
  20  -> and ⟵ (application)  — right-associative for ->
  25  = != < > <= >=
  30  + -
  40  * / %
  50  ∘ (compose)
  60  . (field/method access)
  70  unary minus
"""

from __future__ import annotations

from typing import List, Optional, Any

from .ast_nodes import (
    Program, Preamble, InheritRule, TokenDef, TransformDef, PrecDef,
    FunctionDef, Assignment, Outward, Inward, When, Cycle, Uncycle,
    ReturnStmt, BinOp, Apply, RetroApply, Compose, NullBind, Cons,
    FieldAccess, MethodCall, Identifier, StringLit, IntLit, FloatLit,
    CharLit, ZeroTerm, BoolLit, LambdaExpr, BlockExpr,
)
from .errors import ParseFault, SyntaxFault
from .lexer import (
    Token,
    KW_SYNTAX, KW_INHERIT, KW_TOKEN, KW_MAP, KW_PREC,
    KW_DEFINE, KW_UNDEFINE, KW_WHEN, KW_OTHERWISE,
    KW_CYCLE, KW_UNTIL, KW_UNCYCLE, KW_OUTWARD, KW_INWARD,
    TK_STRING, TK_FLOAT, TK_INTEGER, TK_CHAR, TK_ZERO,
    TK_TRUE, TK_FALSE, TK_IDENT,
    TK_ASSIGN, TK_FWD_APPLY, TK_RET_APPLY, TK_COMPOSE, TK_NULL_BIND,
    TK_CONS, TK_EQ, TK_NEQ, TK_LT, TK_GT, TK_LEQ, TK_GEQ,
    TK_PLUS, TK_MINUS, TK_STAR, TK_SLASH, TK_PERCENT,
    TK_DOT, TK_COMMA, TK_SEMI, TK_COLON,
    TK_LPAREN, TK_RPAREN, TK_LBRACE, TK_RBRACE,
    TK_LBRACKET, TK_RBRACKET, TK_EOF,
)


class Parser:
    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    # ── Token helpers ─────────────────────────────────────────────────────────

    def _peek(self, offset: int = 0) -> Token:
        idx = self.pos + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[idx]

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _check(self, *types: str) -> bool:
        return self._peek().type in types

    def _match(self, *types: str) -> Optional[Token]:
        if self._check(*types):
            return self._advance()
        return None

    def _expect(self, typ: str, context: str = "") -> Token:
        tok = self._peek()
        if tok.type != typ:
            ctx = f" (in {context})" if context else ""
            raise SyntaxFault(
                f"Expected {typ}, got {tok.type} ({tok.value!r})"
                f" at {tok.line}:{tok.col}{ctx}"
            )
        return self._advance()

    # ── Top-level ─────────────────────────────────────────────────────────────

    def parse(self) -> Program:
        preamble = self._parse_preamble()
        definitions: List[FunctionDef] = []
        while not self._check(TK_EOF):
            defn = self._parse_top_level()
            if defn is not None:
                definitions.append(defn)
        return Program(preamble=preamble, definitions=definitions)

    # ── Preamble ──────────────────────────────────────────────────────────────

    def _parse_preamble(self) -> Preamble:
        """Parse `syntax { … }` or return a NullSyntax preamble."""
        if not self._check(KW_SYNTAX):
            return Preamble(rules=[])
        self._advance()  # syntax
        self._expect(TK_LBRACE, "syntax block")
        rules = []
        while not self._check(TK_RBRACE) and not self._check(TK_EOF):
            rule = self._parse_preamble_rule()
            if rule is not None:
                rules.append(rule)
            self._match(TK_SEMI)
        self._expect(TK_RBRACE, "syntax block")
        return Preamble(rules=rules)

    def _parse_preamble_rule(self) -> Optional[Any]:
        tok = self._peek()
        if tok.type == KW_INHERIT:
            self._advance()
            name_parts = [self._expect(TK_IDENT, "inherit").value]
            while self._check(TK_DOT):
                self._advance()
                name_parts.append(self._expect(TK_IDENT, "inherit").value)
            return InheritRule(name=".".join(name_parts))
        if tok.type == KW_TOKEN:
            self._advance()
            ident = self._expect(TK_IDENT, "token def").value
            self._expect(TK_EQ, "token def")
            pattern = self._advance().value
            return TokenDef(identifier=ident, pattern=pattern)
        if tok.type == KW_MAP:
            self._advance()
            token_expr = self._advance().value
            self._expect(TK_FWD_APPLY, "map def")
            zed_expr = self._advance().value
            return TransformDef(token_expr=token_expr, zed_expr=zed_expr)
        if tok.type == KW_PREC:
            self._advance()
            ident = self._expect(TK_IDENT, "prec def").value
            level_tok = self._expect(TK_INTEGER, "prec def")
            return PrecDef(identifier=ident, level=int(level_tok.value))
        # Unknown preamble rule — skip to semicolon
        while not self._check(TK_SEMI) and not self._check(TK_RBRACE) \
                and not self._check(TK_EOF):
            self._advance()
        return None

    # ── Top-level definitions ─────────────────────────────────────────────────

    def _parse_top_level(self) -> Optional[FunctionDef]:
        tok = self._peek()
        if tok.type == KW_DEFINE:
            return self._parse_funcdef(is_retro=False)
        if tok.type == KW_UNDEFINE:
            return self._parse_funcdef(is_retro=True)
        # Skip unexpected top-level tokens
        self._advance()
        return None

    def _parse_funcdef(self, is_retro: bool) -> FunctionDef:
        self._advance()  # define / undefine
        name = self._expect(TK_IDENT, "function definition").value
        params: List[str] = []
        if self._check(TK_LPAREN):
            self._advance()
            if not self._check(TK_RPAREN):
                params.append(self._expect(TK_IDENT, "param list").value)
                while self._match(TK_COMMA):
                    params.append(self._expect(TK_IDENT, "param list").value)
            self._expect(TK_RPAREN, "param list")
        self._expect(TK_LBRACE, "function body")
        body = self._parse_body()
        self._expect(TK_RBRACE, "function body")
        return FunctionDef(name=name, params=params, body=body,
                           is_retro=is_retro)

    # ── Statement lists ───────────────────────────────────────────────────────

    def _parse_body(self) -> List[Any]:
        stmts = []
        while not self._check(TK_RBRACE) and not self._check(TK_EOF):
            stmt = self._parse_statement()
            if stmt is not None:
                stmts.append(stmt)
        return stmts

    def _parse_statement(self) -> Optional[Any]:  # noqa: C901
        tok = self._peek()

        # outward <expr>
        if tok.type == KW_OUTWARD:
            self._advance()
            expr = self._parse_expr()
            return Outward(expr=expr)

        # inward (as statement, possibly assigned)
        if tok.type == KW_INWARD:
            self._advance()
            return Inward()

        # when <cond> { … } otherwise { … }
        if tok.type == KW_WHEN:
            return self._parse_when()

        # cycle <var> ← <init> until <cond> { … }
        if tok.type == KW_CYCLE:
            return self._parse_cycle()

        # uncycle { … }
        if tok.type == KW_UNCYCLE:
            return self._parse_uncycle()

        # Inline define / undefine (nested — not in spec but useful)
        if tok.type == KW_DEFINE:
            return self._parse_funcdef(is_retro=False)
        if tok.type == KW_UNDEFINE:
            return self._parse_funcdef(is_retro=True)

        # <ident> ← <expr>  (assignment)
        # Also allow preamble-only keywords as variable names (e.g. `map`)
        _ident_like = {TK_IDENT, KW_MAP, KW_TOKEN, KW_PREC, KW_INHERIT}
        if tok.type in _ident_like and self._peek(1).type == TK_ASSIGN:
            var = self._advance().value
            self._advance()  # ←
            expr = self._parse_expr()
            return Assignment(var=var, expr=expr)

        # outward <ident> (or any other expression statement)
        expr = self._parse_expr()
        # If next is ← it's actually an assignment to an arbitrary lhs — treat
        # as expression-statement (rare, but handle gracefully)
        if expr is None:
            self._advance()  # skip
            return None
        return expr

    def _parse_when(self) -> When:
        self._advance()  # when
        cond = self._parse_expr()
        self._expect(TK_LBRACE, "when body")
        then_body = self._parse_body()
        self._expect(TK_RBRACE, "when body")
        else_body = None
        if self._match(KW_OTHERWISE):
            self._expect(TK_LBRACE, "otherwise body")
            else_body = self._parse_body()
            self._expect(TK_RBRACE, "otherwise body")
        return When(condition=cond, then_body=then_body, else_body=else_body)

    def _parse_cycle(self) -> Cycle:
        self._advance()  # cycle
        var = self._expect(TK_IDENT, "cycle var").value
        self._expect(TK_ASSIGN, "cycle init")
        init_expr = self._parse_expr()
        self._expect(KW_UNTIL, "cycle guard")
        cond = self._parse_expr()
        self._expect(TK_LBRACE, "cycle body")
        body = self._parse_body()
        self._expect(TK_RBRACE, "cycle body")
        return Cycle(var=var, init_expr=init_expr, condition=cond, body=body)

    def _parse_uncycle(self) -> Uncycle:
        self._advance()  # uncycle
        self._expect(TK_LBRACE, "uncycle body")
        body = self._parse_body()
        self._expect(TK_RBRACE, "uncycle body")
        return Uncycle(body=body)

    # ── Expression parsing ────────────────────────────────────────────────────

    def _parse_expr(self) -> Any:
        """Parse an expression (entry point)."""
        return self._parse_cons()

    def _parse_cons(self) -> Any:
        """:: is right-associative."""
        left = self._parse_comparison()
        if self._match(TK_CONS):
            right = self._parse_cons()
            return Cons(left=left, right=right)
        return left

    def _parse_comparison(self) -> Any:
        left = self._parse_additive()
        op_map = {
            TK_EQ: "=", TK_NEQ: "!=",
            TK_LT: "<", TK_GT: ">",
            TK_LEQ: "<=", TK_GEQ: ">=",
        }
        while self._peek().type in op_map:
            op = op_map[self._advance().type]
            right = self._parse_additive()
            left = BinOp(op=op, left=left, right=right)
        return left

    def _parse_additive(self) -> Any:
        left = self._parse_multiplicative()
        while self._check(TK_PLUS, TK_MINUS):
            op = self._advance().value
            right = self._parse_multiplicative()
            left = BinOp(op=op, left=left, right=right)
        return left

    def _parse_multiplicative(self) -> Any:
        left = self._parse_application()
        while self._check(TK_STAR, TK_SLASH, TK_PERCENT):
            op = self._advance().value
            right = self._parse_application()
            left = BinOp(op=op, left=left, right=right)
        return left

    def _parse_application(self) -> Any:
        """
        Parse forward application (->), retrograde application (⟵),
        and function composition (∘).

        -> is left-associative: f -> x -> y  ≡  (f -> x) -> y
        ⟵ is left-associative as well.
        ∘ is right-associative: f ∘ g ∘ h  ≡  f ∘ (g ∘ h)
        """
        left = self._parse_postfix()
        while True:
            if self._match(TK_FWD_APPLY):
                right = self._parse_postfix()
                left = Apply(func=left, arg=right)
            elif self._match(TK_RET_APPLY):
                right = self._parse_postfix()
                left = RetroApply(func=left, arg=right)
            elif self._match(TK_COMPOSE):
                right = self._parse_application()  # right-recursive
                return Compose(left=left, right=right)
            else:
                break
        return left

    def _parse_postfix(self) -> Any:
        """Parse field access and method calls: expr.field  expr.method(args)."""
        node = self._parse_primary()
        while self._check(TK_DOT):
            self._advance()  # .
            # Field/method names can be identifiers or ident-like keywords
            ftok = self._peek()
            if ftok.type == TK_IDENT or ftok.type in {
                KW_MAP, KW_TOKEN, KW_PREC, KW_INHERIT,
                # Common built-in method names that may be keywords
            }:
                field = self._advance().value
            else:
                field = self._expect(TK_IDENT, "field access").value
            if self._check(TK_LPAREN):
                # method call
                self._advance()
                args = []
                if not self._check(TK_RPAREN):
                    args.append(self._parse_expr())
                    while self._match(TK_COMMA):
                        args.append(self._parse_expr())
                self._expect(TK_RPAREN, "method call")
                node = MethodCall(obj=node, method=field, args=args)
            else:
                node = FieldAccess(obj=node, field=field)
        return node

    def _parse_primary(self) -> Any:  # noqa: C901
        tok = self._peek()

        # Grouped expression
        if tok.type == TK_LPAREN:
            self._advance()
            expr = self._parse_expr()
            self._expect(TK_RPAREN, "grouped expression")
            return expr

        # Literals
        if tok.type == TK_STRING:
            self._advance()
            return StringLit(value=tok.value)
        if tok.type == TK_INTEGER:
            self._advance()
            return IntLit(value=int(tok.value))
        if tok.type == TK_FLOAT:
            self._advance()
            return FloatLit(value=float(tok.value))
        if tok.type == TK_CHAR:
            self._advance()
            return CharLit(value=tok.value)
        if tok.type == TK_ZERO:
            self._advance()
            return ZeroTerm()
        if tok.type == TK_TRUE:
            self._advance()
            return BoolLit(value=True)
        if tok.type == TK_FALSE:
            self._advance()
            return BoolLit(value=False)

        # Inward (as expression)
        if tok.type == KW_INWARD:
            self._advance()
            return Inward()

        # Null-bind: ∅x.body
        if tok.type == TK_NULL_BIND:
            self._advance()
            var = self._expect(TK_IDENT, "null-bind var").value
            self._expect(TK_DOT, "null-bind separator")
            body = self._parse_expr()
            return NullBind(var=var, body=body)

        # Unary minus
        if tok.type == TK_MINUS:
            self._advance()
            operand = self._parse_primary()
            return BinOp(op="unary-", left=IntLit(0), right=operand)

        # Identifier (may be a function call later via ->)
        if tok.type == TK_IDENT:
            self._advance()
            return Identifier(name=tok.value)

        # Preamble-only keywords used as regular identifiers in body context
        # (e.g., `map` is a stdlib function, `token`/`prec`/`inherit` may appear
        #  as user-defined names)
        _BODY_AS_IDENT = {KW_MAP, KW_TOKEN, KW_PREC, KW_INHERIT}
        if tok.type in _BODY_AS_IDENT:
            self._advance()
            return Identifier(name=tok.value)

        # Inline block (rare, but allow { stmts })
        if tok.type == TK_LBRACE:
            self._advance()
            stmts = self._parse_body()
            self._expect(TK_RBRACE, "block expression")
            return BlockExpr(stmts=stmts)

        # When as expression
        if tok.type == KW_WHEN:
            return self._parse_when()

        # Fallthrough — return None signals a missing expression
        return None
