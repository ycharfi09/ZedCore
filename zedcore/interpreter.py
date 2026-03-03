"""ZedCore tree-walking interpreter.

Handles both the forward pass and the retrograde pass.

§8 — Symmetric Execution Model:
  - Forward pass executes normally, writing an execution ledger.
  - Retrograde pass:
      • If a function has an explicit `undefine` block, that body runs.
      • Otherwise, the `define` body's statements run in reverse; each
        `outward` reads from the reversed forward-output queue and prints
        to the retrograde output stream (retrostdout).

§3 — Bootstrap Kernel:
  LAW 2: `z` evaluates to `z` under any preamble and in any direction.
"""

from __future__ import annotations

import sys
from typing import Any, List, Optional, Tuple

from .ast_nodes import (
    Program, FunctionDef, Assignment, Outward, Inward, When, Cycle, Uncycle,
    ReturnStmt, BinOp, Apply, RetroApply, Compose, NullBind, Cons,
    FieldAccess, MethodCall, Identifier, StringLit, IntLit, FloatLit,
    CharLit, ZeroTerm, BoolLit, LambdaExpr, BlockExpr,
)
from .values import (
    Z, _ZeroTermClass, ZedList, ZedFunction, ZedBuiltin, ZedPartial,
    zed_truthy, zed_repr, zed_add, zed_sub, zed_mul, zed_div, zed_mod,
    zed_compare, zed_eq,
)
from .environment import Environment
from .ledger import ExecutionLedger, RULE_IO_OUT, RULE_IO_IN, RULE_BIND, RULE_CALL
from .errors import (
    ZedRuntimeError, _HaltSignal, _ReturnSignal,
    RetrogradeMatchFault,
)
from .stdlib import BUILTINS, string_method


# ── Module-level helper (used by stdlib.py) ───────────────────────────────────

def _apply_value(func: Any, args: List[Any]) -> Any:
    """Apply a callable ZedCore value to a list of arguments, one at a time."""
    result = func
    for arg in args:
        if isinstance(result, ZedBuiltin):
            result = result.func(arg)
        elif isinstance(result, ZedFunction):
            # Create a one-shot interpreter to call the function
            interp = Interpreter.__last_instance__
            if interp is None:
                raise ZedRuntimeError("No active interpreter for function call")
            result = interp.call_function(result, [arg])
        elif isinstance(result, ZedPartial):
            new_applied = result.applied + [arg]
            result = _apply_value(result.func, [arg] if not result.applied
                                  else result.applied + [arg])
        elif result is Z:
            # z annihilates application in forward direction (Rule Ƶ-zero)
            result = Z
        else:
            raise ZedRuntimeError(f"Cannot apply {result!r} to {arg!r}")
    return result


class Interpreter:
    """ZedCore tree-walking interpreter.

    Maintains a reference to the last created instance so that
    stdlib callbacks can call back into the interpreter.
    """

    __last_instance__: Optional["Interpreter"] = None

    def __init__(
        self,
        program: Program,
        stdin: Any = None,
        stdout: Any = None,
        retrostdout: Any = None,
        ledger: Optional[ExecutionLedger] = None,
    ) -> None:
        self.program = program
        self._stdin = stdin or sys.stdin
        self._stdout = stdout or sys.stdout
        self._retrostdout = retrostdout or sys.stdout
        self.ledger = ledger if ledger is not None else ExecutionLedger()
        self._direction: str = "forward"   # "forward" | "retro"
        self._retro_input_queue: List[str] = []  # reversed forward output

        # Root environment seeded with builtins
        self.root_env = Environment()
        for name, val in BUILTINS.items():
            self.root_env.define(name, val)

        # Register all user-defined functions in the root env
        self._register_functions(self.root_env)

        Interpreter.__last_instance__ = self

    # ── Function registration ─────────────────────────────────────────────────

    def _register_functions(self, env: Environment) -> None:
        """Register all top-level define / undefine in the environment."""
        # First pass: create ZedFunction objects
        fwd_map: dict = {}
        ret_map: dict = {}
        for defn in self.program.definitions:
            zf = ZedFunction(
                name=defn.name,
                params=defn.params,
                body=defn.body,
                env=env,
                is_retro=defn.is_retro,
            )
            if defn.is_retro:
                ret_map[defn.name] = zf
            else:
                fwd_map[defn.name] = zf

        # Second pass: link paired definitions and register forward ones
        for name, zf in fwd_map.items():
            if name in ret_map:
                zf.paired = ret_map[name]
                ret_map[name].paired = zf
            env.define(name, zf)

        # Register retrograde functions too (can be called explicitly)
        for name, zf in ret_map.items():
            env.define(f"undefine:{name}", zf)

    # ── Public execution entry points ─────────────────────────────────────────

    def run_forward(self) -> Any:
        """Execute the forward pass.  Returns the exit code."""
        self._direction = "forward"
        try:
            main_fn = self.root_env.get("main")
            if isinstance(main_fn, ZedFunction):
                self.call_function(main_fn, [])
            return Z  # nominal exit
        except _HaltSignal as h:
            return h.exit_code
        except Exception as e:
            self._emit_forward(f"[FW-F-004] {e}")
            return 1

    def run_retro(self, fwd_exit: Any) -> Any:
        """Execute the retrograde pass.  Returns the exit code."""
        self._direction = "retro"
        # Build the reversed forward-output queue from the ledger
        forward_outputs = self.ledger.io_outputs()
        # The retrograde input is the forward output in reversed order.
        # The ledger stores repr(value); for display we strip the outer quotes.
        self._retro_input_queue = list(reversed(forward_outputs))

        try:
            # Try explicit undefine main first
            undefine_key = "undefine:main"
            if self.root_env.has(undefine_key):
                retro_fn = self.root_env.get(undefine_key)
                if isinstance(retro_fn, ZedFunction):
                    self.call_function(retro_fn, [])
            else:
                # Auto-retrograde: find the main define and run it backwards
                main_fn = self.root_env.get("main")
                if isinstance(main_fn, ZedFunction):
                    self._auto_retro_body(main_fn.body, main_fn.env)
            return Z
        except _HaltSignal as h:
            return h.exit_code
        except RetrogradeMatchFault:
            raise
        except Exception as e:
            self._emit_retro(f"[RT-F-004] {e}")
            return 1

    # ── Function call dispatch ────────────────────────────────────────────────

    def call_function(
        self, func: ZedFunction, args: List[Any], env: Optional[Environment] = None
    ) -> Any:
        """Invoke a ZedFunction with the given argument list."""
        if len(args) < len(func.params):
            # Partial application
            return ZedPartial(func=func, applied=args)

        call_env = Environment(parent=func.env)
        for param, arg in zip(func.params, args):
            call_env.define(param, arg)

        self.ledger.record_call(func.name, args)
        try:
            result = self._exec_body(func.body, call_env)
            return result if result is not None else Z
        except _ReturnSignal as r:
            return r.value

    # ── Body execution ────────────────────────────────────────────────────────

    def _exec_body(self, stmts: List[Any], env: Environment) -> Any:
        last: Any = Z
        for stmt in stmts:
            val = self._exec_stmt(stmt, env)
            if val is not None:
                last = val
        return last

    def _exec_stmt(self, stmt: Any, env: Environment) -> Any:  # noqa: C901
        # ── outward ───────────────────────────────────────────────────────────
        if isinstance(stmt, Outward):
            val = self._eval(stmt.expr, env)
            if self._direction == "retro":
                self._emit_retro(zed_repr(val))
            else:
                self._emit_forward(zed_repr(val))
                self.ledger.record_io_out(val)
            return val

        # ── inward ────────────────────────────────────────────────────────────
        if isinstance(stmt, Inward):
            if self._direction == "retro":
                val = self._read_retro()
            else:
                val = self._read_forward()
                self.ledger.record_io_in(val)
            return val

        # ── assignment ────────────────────────────────────────────────────────
        if isinstance(stmt, Assignment):
            # Special case: `var ← inward`
            if isinstance(stmt.expr, Inward):
                if self._direction == "retro":
                    val = self._read_retro()
                else:
                    val = self._read_forward()
                    self.ledger.record_io_in(val)
            else:
                val = self._eval(stmt.expr, env)
            env.set(stmt.var, val)
            self.ledger.record_bind(stmt.var, val)
            return val

        # ── when / otherwise ─────────────────────────────────────────────────
        if isinstance(stmt, When):
            cond = self._eval(stmt.condition, env)
            branch_env = env.child()
            if zed_truthy(cond):
                return self._exec_body(stmt.then_body, branch_env)
            elif stmt.else_body is not None:
                return self._exec_body(stmt.else_body, branch_env)
            return Z

        # ── cycle (forward loop) ──────────────────────────────────────────────
        if isinstance(stmt, Cycle):
            loop_env = env.child()
            init_val = self._eval(stmt.init_expr, env)
            loop_env.set(stmt.var, init_val)
            last: Any = Z
            while True:
                # `until <cond>` = stop WHEN condition becomes true
                stop = self._eval(stmt.condition, loop_env)
                if zed_truthy(stop):
                    break
                last = self._exec_body(stmt.body, loop_env)
            return last

        # ── uncycle (retrograde loop — runs normally in forward pass) ─────────
        if isinstance(stmt, Uncycle):
            return self._exec_body(stmt.body, env.child())

        # ── nested define / undefine ──────────────────────────────────────────
        if isinstance(stmt, FunctionDef):
            zf = ZedFunction(
                name=stmt.name,
                params=stmt.params,
                body=stmt.body,
                env=env,
                is_retro=stmt.is_retro,
            )
            if stmt.is_retro:
                env.set(f"undefine:{stmt.name}", zf)
            else:
                env.set(stmt.name, zf)
            return zf

        # ── Expressions used as statements ────────────────────────────────────
        val = self._eval(stmt, env)
        # Auto-call zero-arg functions when used as statements (e.g. `greet`)
        if isinstance(val, ZedFunction) and len(val.params) == 0:
            val = self.call_function(val, [])
        return val

    # ── Expression evaluation ─────────────────────────────────────────────────

    def _eval(self, node: Any, env: Environment) -> Any:  # noqa: C901
        if node is None:
            return Z

        # ── Terminals ─────────────────────────────────────────────────────────
        if isinstance(node, ZeroTerm):
            return Z   # LAW 2: z evaluates to z under any preamble
        if isinstance(node, IntLit):
            return node.value
        if isinstance(node, FloatLit):
            return node.value
        if isinstance(node, StringLit):
            return node.value
        if isinstance(node, CharLit):
            return node.value
        if isinstance(node, BoolLit):
            return node.value

        # ── Identifier ────────────────────────────────────────────────────────
        if isinstance(node, Identifier):
            try:
                return env.get(node.name)
            except NameError:
                raise ZedRuntimeError(f"Undefined name: {node.name!r}")

        # ── Inward (as expression) ────────────────────────────────────────────
        if isinstance(node, Inward):
            if self._direction == "retro":
                return self._read_retro()
            val = self._read_forward()
            self.ledger.record_io_in(val)
            return val

        # ── Outward (as expression) ───────────────────────────────────────────
        if isinstance(node, Outward):
            val = self._eval(node.expr, env)
            if self._direction == "retro":
                self._emit_retro(zed_repr(val))
            else:
                self._emit_forward(zed_repr(val))
                self.ledger.record_io_out(val)
            return val

        # ── Binary operations ─────────────────────────────────────────────────
        if isinstance(node, BinOp):
            return self._eval_binop(node, env)

        # ── Forward application: func -> arg ──────────────────────────────────
        if isinstance(node, Apply):
            func = self._eval(node.func, env)
            arg = self._eval(node.arg, env)
            return self._call_val(func, arg)

        # ── Retrograde application: func ⟵ arg ───────────────────────────────
        if isinstance(node, RetroApply):
            # Rule Ƶ-β̄: evaluate arg first, apply in reverse
            arg = self._eval(node.arg, env)
            func = self._eval(node.func, env)
            if isinstance(func, ZedFunction) and func.paired is not None and \
                    not func.is_retro:
                # Apply the paired retrograde function
                return self._call_val(func.paired, arg)
            return self._call_val(func, arg)

        # ── Composition: f ∘ g ────────────────────────────────────────────────
        if isinstance(node, Compose):
            f = self._eval(node.left, env)
            g = self._eval(node.right, env)
            return ZedBuiltin(
                name=f"compose({f!r}, {g!r})",
                func=lambda x: self._call_val(f, self._call_val(g, x)),
            )

        # ── Null-bind: ∅x.M ──────────────────────────────────────────────────
        if isinstance(node, NullBind):
            child_env = env.child()
            child_env.define(node.var, Z)  # bind x to z
            return self._eval(node.body, child_env)

        # ── Cons: left :: right ───────────────────────────────────────────────
        if isinstance(node, Cons):
            left = self._eval(node.left, env)
            right = self._eval(node.right, env)
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            if isinstance(left, str) and right is Z:
                return left
            return ZedList(head=left, tail=right)

        # ── Field access: obj.field ───────────────────────────────────────────
        if isinstance(node, FieldAccess):
            obj = self._eval(node.obj, env)
            return string_method(obj, node.field, [])

        # ── Method call: obj.method(args) ─────────────────────────────────────
        if isinstance(node, MethodCall):
            obj = self._eval(node.obj, env)
            args = [self._eval(a, env) for a in node.args]
            return string_method(obj, node.method, args)

        # ── When as expression ────────────────────────────────────────────────
        if isinstance(node, When):
            cond = self._eval(node.condition, env)
            if zed_truthy(cond):
                return self._exec_body(node.then_body, env.child())
            elif node.else_body is not None:
                return self._exec_body(node.else_body, env.child())
            return Z

        # ── Block expression ──────────────────────────────────────────────────
        if isinstance(node, BlockExpr):
            return self._exec_body(node.stmts, env.child())

        # ── Assignment as expression ──────────────────────────────────────────
        if isinstance(node, Assignment):
            val = self._eval(node.expr, env)
            env.set(node.var, val)
            return val

        # ── Lambda expression ─────────────────────────────────────────────────
        if isinstance(node, LambdaExpr):
            return ZedFunction(
                name="<lambda>",
                params=[node.param],
                body=[ReturnStmt(node.body)],
                env=env,
            )

        # ── Return statement ──────────────────────────────────────────────────
        if isinstance(node, ReturnStmt):
            val = self._eval(node.expr, env)
            raise _ReturnSignal(val)

        # Unknown node — return z (safe degradation)
        return Z

    def _eval_binop(self, node: BinOp, env: Environment) -> Any:
        if node.op == "unary-":
            right = self._eval(node.right, env)
            return zed_sub(0, right)
        left = self._eval(node.left, env)
        right = self._eval(node.right, env)
        op = node.op
        if op == "+":
            return zed_add(left, right)
        if op == "-":
            return zed_sub(left, right)
        if op == "*":
            return zed_mul(left, right)
        if op == "/":
            return zed_div(left, right)
        if op == "%":
            return zed_mod(left, right)
        if op in ("=", "!=", "<", ">", "<=", ">="):
            return zed_compare(op, left, right)
        raise ZedRuntimeError(f"Unknown binary operator: {op!r}")

    def _call_val(self, func: Any, arg: Any) -> Any:
        """Call a ZedCore value as a function with one argument."""
        if func is Z:
            # Rule Ƶ-zero (forward): z M → z
            return Z
        if isinstance(func, ZedBuiltin):
            return func.func(arg)
        if isinstance(func, ZedFunction):
            if len(func.params) == 0:
                # zero-arg function — call it and then apply the result to arg
                result = self.call_function(func, [])
                return self._call_val(result, arg)
            if len(func.params) == 1:
                return self.call_function(func, [arg])
            # multi-arg: partial application
            return ZedPartial(func=func, applied=[arg])
        if isinstance(func, ZedPartial):
            new_args = func.applied + [arg]
            inner = func.func
            if isinstance(inner, ZedFunction):
                if len(new_args) >= len(inner.params):
                    return self.call_function(inner, new_args)
                return ZedPartial(func=inner, applied=new_args)
            if isinstance(inner, ZedBuiltin):
                result = inner
                for a in new_args:
                    result = result.func(a)
                    if not isinstance(result, ZedBuiltin):
                        break
                return result
        raise ZedRuntimeError(f"Cannot call {func!r} with argument {arg!r}")

    # ── Auto-retrograde ───────────────────────────────────────────────────────

    def _auto_retro_body(self, stmts: List[Any], env: Environment) -> None:
        """Run a define body in reverse for the retrograde pass.

        Each `outward` reads from the retrograde input queue and emits to
        retrostdout (per §8.2, 8.4).
        """
        for stmt in reversed(stmts):
            self._auto_retro_stmt(stmt, env)

    def _auto_retro_stmt(self, stmt: Any, env: Environment) -> None:
        """Execute one statement in auto-retrograde mode."""
        if isinstance(stmt, Outward):
            # retrograde outward: read from retro input, emit to retrostdout
            val = self._read_retro()
            self._emit_retro(zed_repr(val))
        elif isinstance(stmt, Assignment):
            if isinstance(stmt.expr, Inward):
                # forward inward → retrograde outward: write to retrostdout
                # (we don't have the original value, use z as placeholder)
                self._emit_retro("z")
            # else: skip assignment reversal (simplified)
        elif isinstance(stmt, When):
            # Reverse the when: run else branch first (if present), then when
            if stmt.else_body:
                self._auto_retro_body(stmt.else_body, env.child())
            self._auto_retro_body(stmt.then_body, env.child())
        elif isinstance(stmt, Cycle):
            # Skip loop body reversal in auto-retro (simplified)
            pass
        elif isinstance(stmt, FunctionDef):
            pass
        # Other statements: skip in auto-retro

    # ── I/O helpers ───────────────────────────────────────────────────────────

    def _emit_forward(self, text: str) -> None:
        self._stdout.write(text + "\n")
        self._stdout.flush()

    def _emit_retro(self, text: str) -> None:
        self._retrostdout.write(text + "\n")
        self._retrostdout.flush()

    def _read_forward(self) -> str:
        try:
            line = self._stdin.readline()
            if not line:
                return "z"
            return line.rstrip("\n")
        except EOFError:
            return "z"

    def _read_retro(self) -> str:
        if self._retro_input_queue:
            raw = self._retro_input_queue.pop(0)
            # Unwrap repr quotes if the value was a string literal
            if raw.startswith("'") and raw.endswith("'"):
                return raw[1:-1]
            return raw
        return "z"
