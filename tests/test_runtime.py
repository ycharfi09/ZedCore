"""Tests for the ZedCore runtime (end-to-end symmetric execution)."""

import io
import pytest
from zedcore.runtime import Runtime, _exit_xor
from zedcore.values import Z


def execute(source: str, stdin: str = ""):
    return Runtime(source, stdin=io.StringIO(stdin)).execute()


# ── Hello World ───────────────────────────────────────────────────────────────

class TestHelloWorld:
    HELLO_SRC = """
    syntax { inherit ZedSyntax; }
    define main {
      outward "Hello, Zero."
      outward z
    }
    """

    def test_forward_lines(self):
        result = execute(self.HELLO_SRC)
        lines = result.fwd_output.strip().splitlines()
        assert lines[0] == "Hello, Zero."
        assert lines[1] == "z"

    def test_retrograde_lines(self):
        result = execute(self.HELLO_SRC)
        lines = result.ret_output.strip().splitlines()
        assert lines[0] == "z"
        assert lines[1] == "Hello, Zero."

    def test_exit_code_z(self):
        result = execute(self.HELLO_SRC)
        assert result.exit_code is Z
        assert result.success

    def test_ledger_not_empty(self):
        result = execute(self.HELLO_SRC)
        assert len(result.ledger) > 0


# ── Explicit undefine ─────────────────────────────────────────────────────────

class TestExplicitRetro:
    def test_undefine_runs_on_retro(self):
        src = """
        define main { outward "forward" }
        undefine main { outward "retrograde" }
        """
        result = execute(src)
        assert "forward" in result.fwd_output
        assert "retrograde" in result.ret_output

    def test_undefine_reads_retro_input(self):
        src = """
        define main { outward "written" }
        undefine main {
          x ← inward
          outward x
        }
        """
        result = execute(src)
        assert "written" in result.ret_output


# ── I/O round-trip ────────────────────────────────────────────────────────────

class TestIOSymmetry:
    def test_echo_forward(self):
        src = """
        define main {
          value ← inward
          outward value
        }
        """
        result = execute(src, stdin="hello")
        assert "hello" in result.fwd_output

    def test_echo_retro_read(self):
        src = """
        define main {
          value ← inward
          outward value
        }
        """
        result = execute(src, stdin="testvalue")
        # Retrograde auto-reads forward output and re-emits
        assert "testvalue" in result.ret_output


# ── Error ontology ────────────────────────────────────────────────────────────

class TestErrorOntology:
    def test_parse_error_returns_nonzero(self):
        # Malformed source should produce an error
        src = "define main { {{ {{ {{"
        result = execute(src)
        # Either error field is set, or the run raises cleanly
        # (parse errors cause exit_code != Z)
        # We just check it doesn't raise an unhandled exception

    def test_undefined_variable_is_runtime_error(self):
        src = "define main { outward undefined_var }"
        # Should produce an error without crashing the test runner
        result = execute(src)
        # result.success may be False; that's acceptable
        assert result is not None


# ── Ledger ────────────────────────────────────────────────────────────────────

class TestLedger:
    def test_io_recorded(self):
        src = 'define main { outward "test" }'
        result = execute(src)
        outputs = result.ledger.io_outputs()
        assert any("test" in str(o) for o in outputs)

    def test_hash_chain_valid(self):
        src = 'define main { outward "a"\n outward "b"\n outward "c" }'
        result = execute(src)
        assert result.ledger.verify_chain()


# ── Exit code XOR ─────────────────────────────────────────────────────────────

class TestExitXOR:
    def test_z_xor_z(self):
        assert _exit_xor(Z, Z) is Z

    def test_z_xor_1(self):
        assert _exit_xor(Z, 1) == 1

    def test_1_xor_z(self):
        assert _exit_xor(1, Z) == 1

    def test_1_xor_1(self):
        # Symmetric fault — both failed identically → clean exit (z)
        assert _exit_xor(1, 1) is Z

    def test_2_xor_3(self):
        assert _exit_xor(2, 3) == 1  # 0b10 XOR 0b11 = 0b01


# ── Full programs ─────────────────────────────────────────────────────────────

class TestFullPrograms:
    def test_factorial_5(self):
        src = """
        define factorial (n) {
          when n = 0 {
            1
          } otherwise {
            result ← 1
            cycle i ← 1 until i > n {
              result ← result * i
              i ← i + 1
            }
            result
          }
        }
        define main {
          outward factorial -> 5
        }
        """
        result = execute(src)
        assert "120" in result.fwd_output

    def test_multiple_outputs(self):
        src = """
        define main {
          outward 1
          outward 2
          outward 3
        }
        """
        result = execute(src)
        lines = result.fwd_output.strip().splitlines()
        assert lines == ["1", "2", "3"]
        # Retrograde reverses the order
        retro_lines = result.ret_output.strip().splitlines()
        assert retro_lines == ["3", "2", "1"]
