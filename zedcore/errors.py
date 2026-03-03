"""ZedCore error ontology (§12 of the spec).

Errors are classified on two axes:
  - Direction: Forward (FW) or Retrograde (RT)
  - Severity:  Fatal (F) or Recoverable (R)

Code format: <DIR>-<SEV>-<NUM>
"""

from __future__ import annotations


class ZedError(Exception):
    """Base class for all ZedCore runtime errors."""

    code: str = "ZED-000"

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.zed_code = code or self.code

    def __str__(self) -> str:  # noqa: D401
        return f"[{self.zed_code}] {super().__str__()}"


# ── Forward Fatal ─────────────────────────────────────────────────────────────

class ParseFault(ZedError):
    """FW-F-001: Preamble does not conform to MSL grammar."""

    code = "FW-F-001"


class SyntaxFault(ZedError):
    """FW-F-001 (body): Body source does not parse under the active SDT."""

    code = "FW-F-001"


class SDTCompileFailure(ZedError):
    """FW-F-002: Preamble is valid MSL but produces an inconsistent SDT."""

    code = "FW-F-002"


class SafeSyntaxAuthFailure(ZedError):
    """FW-F-003: One or more ZAUTH layers not satisfied."""

    code = "FW-F-003"


class ZedRuntimeError(ZedError):
    """FW-F-004: General forward-pass runtime error."""

    code = "FW-F-004"


class ZetaHorizon(ZedError):
    """FW-F-099: Program executed ≥ 2^64 steps; presumed infinite loop."""

    code = "FW-F-099"


# ── Forward Recoverable ───────────────────────────────────────────────────────

class TermUnresolvable(ZedError):
    """FW-R-010: Token encountered with no SDT entry; mapped to ⊥⊤."""

    code = "FW-R-010"


class LedgerCapacityExceeded(ZedError):
    """FW-R-011: Execution ledger overflowed on-chip SRAM; spilled to disk."""

    code = "FW-R-011"


# ── Retrograde Fatal ──────────────────────────────────────────────────────────

class RetrogradeMatchFault(ZedError):
    """RT-F-050: Retrograde input does not match forward output."""

    code = "RT-F-050"


class LedgerCorrupt(ZedError):
    """RT-F-051: Ledger hash chain broken; retrograde cannot proceed."""

    code = "RT-F-051"


class NoRetroBlock(ZedError):
    """RT-F-052: Function has forward `define` but no `undefine`; ZedTPU only."""

    code = "RT-F-052"


# ── Retrograde Recoverable ────────────────────────────────────────────────────

class RetroApproximation(ZedError):
    """RT-R-060: Retrograde reconstruction used approximation (loss detected)."""

    code = "RT-R-060"


# ── Helpers ───────────────────────────────────────────────────────────────────

class _HaltSignal(BaseException):
    """Internal signal used by ZHALT / the `z` exit mechanism."""

    def __init__(self, exit_code: object) -> None:
        super().__init__()
        self.exit_code = exit_code


class _ReturnSignal(BaseException):
    """Internal signal used to return a value from a function body."""

    def __init__(self, value: object) -> None:
        super().__init__()
        self.value = value
