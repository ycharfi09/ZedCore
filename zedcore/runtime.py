"""ZedCore runtime — orchestrates the full symmetric execution.

§3 Bootstrap Kernel, LAW 1:
  Every execution is a pair (F, R) where F is the forward pass and R is the
  retrograde pass.  F must complete before R begins.  R must complete before
  the program is considered terminated.
  The exit value of the program is the XOR of the exit codes of F and R.

§8.3 Exit Code Semantics:
  exit_code = F.exit XOR R.exit
  z XOR z  =  z   (nominal success)
  z XOR 1  =  1   (retrograde fault)
  1 XOR z  =  1   (forward fault)
  1 XOR 1  =  z   (symmetric fault — valid, if unusual, clean exit)
"""

from __future__ import annotations

import io
import sys
from dataclasses import dataclass, field
from typing import Any, List, Optional, TextIO

from .lexer import Lexer
from .parser import Parser
from .interpreter import Interpreter
from .ledger import ExecutionLedger
from .errors import ParseFault, SyntaxFault, ZedError


# ── Exit code arithmetic ──────────────────────────────────────────────────────

def _exit_xor(a: Any, b: Any) -> Any:
    """Compute F.exit XOR R.exit per §8.3.

    The zero term `z` maps to integer 0 for the XOR computation.
    """
    from .values import Z, _ZeroTermClass
    a_int = 0 if (a is Z or isinstance(a, _ZeroTermClass)) else (
        a if isinstance(a, int) else 1
    )
    b_int = 0 if (b is Z or isinstance(b, _ZeroTermClass)) else (
        b if isinstance(b, int) else 1
    )
    result = a_int ^ b_int
    if result == 0:
        return Z
    return result


# ── Execution result ──────────────────────────────────────────────────────────

@dataclass
class ExecutionResult:
    """Result of a complete symmetric ZedCore execution."""

    fwd_exit: Any
    ret_exit: Any
    exit_code: Any
    fwd_output: str
    ret_output: str
    ledger: ExecutionLedger
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        from .values import Z, _ZeroTermClass
        return self.exit_code is Z or isinstance(self.exit_code, _ZeroTermClass)


# ── Runtime ───────────────────────────────────────────────────────────────────

class Runtime:
    """ZedCore program runtime.

    Parses source, then runs the forward pass followed by the retrograde pass.
    """

    def __init__(
        self,
        source: str,
        stdin: Optional[TextIO] = None,
        silent_retro: bool = False,
    ) -> None:
        self.source = source
        self._stdin = stdin or sys.stdin
        self._silent_retro = silent_retro  # suppress retrograde output (for tests)

    def execute(self) -> ExecutionResult:
        """Parse and execute the program symmetrically."""
        # ── Parse ──────────────────────────────────────────────────────────────
        try:
            tokens = Lexer(self.source).tokenize()
            program = Parser(tokens).parse()
        except (ParseFault, SyntaxFault) as e:
            return ExecutionResult(
                fwd_exit=1, ret_exit=1,
                exit_code=1,
                fwd_output="",
                ret_output="",
                ledger=ExecutionLedger(),
                error=str(e),
            )

        # ── Prepare I/O streams ────────────────────────────────────────────────
        fwd_out = io.StringIO()
        ret_out = io.StringIO()
        ledger = ExecutionLedger()

        interp = Interpreter(
            program=program,
            stdin=self._stdin,
            stdout=fwd_out,
            retrostdout=ret_out,
            ledger=ledger,
        )

        # ── Forward pass (F) ───────────────────────────────────────────────────
        fwd_exit = interp.run_forward()
        fwd_output = fwd_out.getvalue()

        # ── Retrograde pass (R) ────────────────────────────────────────────────
        ret_exit = interp.run_retro(fwd_exit)
        ret_output = ret_out.getvalue()

        # ── Exit code = F.exit XOR R.exit ─────────────────────────────────────
        exit_code = _exit_xor(fwd_exit, ret_exit)

        return ExecutionResult(
            fwd_exit=fwd_exit,
            ret_exit=ret_exit,
            exit_code=exit_code,
            fwd_output=fwd_output,
            ret_output=ret_output,
            ledger=ledger,
        )


def run_file(
    path: str,
    stdin: Optional[TextIO] = None,
    print_retro: bool = True,
) -> int:
    """Load a ZedCore source file, execute it, and return the process exit code.

    Mirrors the behaviour described in §4.2 PPP (Preamble Parsing Protocol).
    """
    with open(path, encoding="utf-8") as fh:
        source = fh.read()

    runtime = Runtime(source, stdin=stdin)
    result = runtime.execute()

    # Write forward output to real stdout
    sys.stdout.write(result.fwd_output)

    if result.error:
        sys.stderr.write(result.error + "\n")
        return 1

    # Write retrograde output to real stdout (prefixed so it's visible)
    if print_retro and result.ret_output.strip():
        sys.stdout.write("--- retrograde pass ---\n")
        sys.stdout.write(result.ret_output)

    # Convert exit code to process exit code
    from .values import Z, _ZeroTermClass
    if result.exit_code is Z or isinstance(result.exit_code, _ZeroTermClass):
        return 0
    if isinstance(result.exit_code, int):
        return result.exit_code & 0xFF
    return 1
