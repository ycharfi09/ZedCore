"""Tests for the ZedCore interpreter (expression evaluation)."""

import pytest
import io
from zedcore.lexer import Lexer
from zedcore.parser import Parser
from zedcore.interpreter import Interpreter
from zedcore.runtime import Runtime
from zedcore.values import Z, ZedList, zed_repr


def run(source: str, stdin: str = "") -> tuple[str, str]:
    """Run source and return (forward_output, retro_output)."""
    runtime = Runtime(source, stdin=io.StringIO(stdin))
    result = runtime.execute()
    return result.fwd_output, result.ret_output


def fwd(source: str, stdin: str = "") -> str:
    """Return stripped forward output."""
    out, _ = run(source, stdin)
    return out.strip()


# ── Zero term ─────────────────────────────────────────────────────────────────

class TestZeroTerm:
    def test_z_outputs_z(self):
        assert fwd("define main { outward z }") == "z"

    def test_z_is_z(self):
        assert fwd("define main { x ← z\n outward x }") == "z"


# ── Literals ──────────────────────────────────────────────────────────────────

class TestLiterals:
    def test_string_literal(self):
        assert fwd('define main { outward "Hello, Zero." }') == "Hello, Zero."

    def test_integer_literal(self):
        assert fwd("define main { outward 42 }") == "42"

    def test_arithmetic(self):
        assert fwd("define main { outward 2 + 3 }") == "5"
        assert fwd("define main { outward 10 - 4 }") == "6"
        assert fwd("define main { outward 3 * 4 }") == "12"
        assert fwd("define main { outward 10 / 2 }") == "5"
        assert fwd("define main { outward 10 % 3 }") == "1"

    def test_boolean(self):
        assert fwd("define main { outward true }") == "true"
        assert fwd("define main { outward false }") == "false"


# ── Variables ─────────────────────────────────────────────────────────────────

class TestVariables:
    def test_assignment_and_read(self):
        src = """
        define main {
          x ← 7
          outward x
        }
        """
        assert fwd(src) == "7"

    def test_reassignment(self):
        src = """
        define main {
          x ← 1
          x ← 2
          outward x
        }
        """
        assert fwd(src) == "2"


# ── Functions ─────────────────────────────────────────────────────────────────

class TestFunctions:
    def test_zero_arg_function(self):
        src = """
        define greet {
          outward "hi"
        }
        define main {
          greet
        }
        """
        assert fwd(src) == "hi"

    def test_one_arg_function(self):
        src = """
        define double (n) {
          n * 2
        }
        define main {
          outward double -> 5
        }
        """
        assert fwd(src) == "10"

    def test_two_arg_function_curried(self):
        src = """
        define add (a, b) {
          a + b
        }
        define main {
          outward add -> 3 -> 4
        }
        """
        assert fwd(src) == "7"

    def test_return_value(self):
        src = """
        define inc (n) {
          n + 1
        }
        define main {
          x ← inc -> 10
          outward x
        }
        """
        assert fwd(src) == "11"


# ── Conditionals ─────────────────────────────────────────────────────────────

class TestConditionals:
    def test_when_true(self):
        src = """
        define main {
          when true { outward "yes" }
        }
        """
        assert fwd(src) == "yes"

    def test_when_false_no_else(self):
        src = """
        define main {
          when false { outward "yes" }
          outward "done"
        }
        """
        assert fwd(src) == "done"

    def test_when_otherwise(self):
        src = """
        define main {
          x ← 5
          when x > 3 { outward "big" } otherwise { outward "small" }
        }
        """
        assert fwd(src) == "big"

    def test_otherwise_branch(self):
        src = """
        define main {
          x ← 2
          when x > 3 { outward "big" } otherwise { outward "small" }
        }
        """
        assert fwd(src) == "small"

    def test_z_is_falsy(self):
        src = """
        define main {
          when z { outward "yes" } otherwise { outward "no" }
        }
        """
        assert fwd(src) == "no"

    def test_equality(self):
        src = """
        define main {
          when z = z { outward "equal" }
        }
        """
        assert fwd(src) == "equal"


# ── Loops ─────────────────────────────────────────────────────────────────────

class TestLoops:
    def test_cycle_loop(self):
        src = """
        define main {
          cycle i ← 1 until i > 3 {
            outward i
            i ← i + 1
          }
        }
        """
        lines = fwd(src).splitlines()
        assert lines == ["1", "2", "3"]

    def test_cycle_accumulator(self):
        src = """
        define main {
          acc ← 0
          cycle i ← 1 until i > 5 {
            acc ← acc + i
            i ← i + 1
          }
          outward acc
        }
        """
        assert fwd(src) == "15"


# ── I/O ───────────────────────────────────────────────────────────────────────

class TestIO:
    def test_inward(self):
        src = """
        define main {
          x ← inward
          outward x
        }
        """
        assert fwd(src, stdin="hello") == "hello"


# ── Sequences ─────────────────────────────────────────────────────────────────

class TestSequences:
    def test_cons(self):
        src = """
        define main {
          lst ← 1 :: 2 :: 3 :: z
          outward lst
        }
        """
        out = fwd(src)
        assert "1" in out and "2" in out and "3" in out

    def test_map(self):
        src = """
        define double (x) { x * 2 }
        define main {
          items ← 1 :: 2 :: 3 :: z
          result ← map -> double -> items
          outward result
        }
        """
        out = fwd(src)
        assert "2" in out and "4" in out and "6" in out


# ── Hello World ───────────────────────────────────────────────────────────────

class TestHelloWorld:
    def test_forward_output(self):
        src = """
        syntax { inherit ZedSyntax; }
        define main {
          outward "Hello, Zero."
          outward z
        }
        """
        fwd_out, _ = run(src)
        lines = fwd_out.strip().splitlines()
        assert lines[0] == "Hello, Zero."
        assert lines[1] == "z"

    def test_retrograde_output(self):
        """Retrograde pass should print z then Hello, Zero. (reversed)."""
        src = """
        syntax { inherit ZedSyntax; }
        define main {
          outward "Hello, Zero."
          outward z
        }
        """
        _, ret_out = run(src)
        lines = ret_out.strip().splitlines()
        assert lines[0] == "z"
        assert lines[1] == "Hello, Zero."

    def test_exit_code(self):
        src = """
        syntax { inherit ZedSyntax; }
        define main {
          outward "Hello, Zero."
          outward z
        }
        """
        runtime = Runtime(src)
        result = runtime.execute()
        assert result.success
        assert result.exit_code is Z


# ── Symmetric exit codes ──────────────────────────────────────────────────────

class TestExitCodes:
    def test_z_xor_z_is_z(self):
        from zedcore.runtime import _exit_xor
        assert _exit_xor(Z, Z) is Z

    def test_z_xor_1_is_1(self):
        from zedcore.runtime import _exit_xor
        assert _exit_xor(Z, 1) == 1

    def test_1_xor_z_is_1(self):
        from zedcore.runtime import _exit_xor
        assert _exit_xor(1, Z) == 1

    def test_1_xor_1_is_z(self):
        from zedcore.runtime import _exit_xor
        assert _exit_xor(1, 1) is Z
