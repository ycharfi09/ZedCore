"""Execution ledger — the append-only forward-pass log used for retrograde.

§8.1 of the spec:

  "Every ZedCore program, during its forward pass, writes an execution ledger
  — a complete, append-only record of every reduction step taken, every
  binding created, every I/O operation performed. The ledger is structured as
  a Merkle tree rooted at the program's terminal state."

  Ledger entry format:
    [step_id: uint64] [term_before] [rule_applied] [term_after]
    [timestamp: nanoseconds] [hash: SHA3-256 of prev entry]

The retrograde pass consumes the ledger in **reverse** order.
"""

from __future__ import annotations

import hashlib
import struct
import time
from dataclasses import dataclass, field
from typing import Any, List, Optional

# ── Entry types (rule_applied field) ─────────────────────────────────────────
RULE_BIND     = "bind"       # variable binding
RULE_APPLY    = "apply"      # forward application
RULE_RETRO    = "retro"      # retrograde application
RULE_IO_OUT   = "io_out"     # outward (forward output)
RULE_IO_IN    = "io_in"      # inward  (forward input)
RULE_BRANCH   = "branch"     # when/otherwise
RULE_LOOP     = "loop"       # cycle iteration
RULE_CALL     = "call"       # function call
RULE_RETURN   = "return"     # function return
RULE_KERNEL   = "kernel"     # bootstrap kernel operation


@dataclass
class LedgerEntry:
    step_id: int
    rule: str
    term_before: Any
    term_after: Any
    timestamp_ns: int
    prev_hash: bytes
    entry_hash: bytes = field(init=False)

    def __post_init__(self) -> None:
        self.entry_hash = self._compute_hash()

    def _compute_hash(self) -> bytes:
        h = hashlib.sha3_256()
        h.update(struct.pack(">Q", self.step_id))
        h.update(self.rule.encode())
        h.update(str(self.term_before).encode())
        h.update(str(self.term_after).encode())
        h.update(struct.pack(">Q", self.timestamp_ns))
        h.update(self.prev_hash)
        return h.digest()


class ExecutionLedger:
    """Append-only execution ledger.

    Used during the forward pass to record all significant operations.
    The retrograde pass iterates entries in reverse order.
    """

    def __init__(self) -> None:
        self._entries: List[LedgerEntry] = []
        self._step_counter: int = 0
        self._prev_hash: bytes = b"\x00" * 32  # genesis hash

    # ── Recording ─────────────────────────────────────────────────────────────

    def record(self, rule: str, before: Any, after: Any) -> None:
        """Append a new ledger entry."""
        ts = time.time_ns()
        entry = LedgerEntry(
            step_id=self._step_counter,
            rule=rule,
            term_before=before,
            term_after=after,
            timestamp_ns=ts,
            prev_hash=self._prev_hash,
        )
        self._entries.append(entry)
        self._prev_hash = entry.entry_hash
        self._step_counter += 1

    def record_bind(self, name: str, value: Any) -> None:
        self.record(RULE_BIND, f"{name}=?", f"{name}={value!r}")

    def record_io_out(self, value: Any) -> None:
        self.record(RULE_IO_OUT, "stdout", repr(value))

    def record_io_in(self, value: Any) -> None:
        self.record(RULE_IO_IN, "stdin", repr(value))

    def record_call(self, name: str, args: Any) -> None:
        self.record(RULE_CALL, f"call {name}", repr(args))

    def record_return(self, name: str, value: Any) -> None:
        self.record(RULE_RETURN, f"return {name}", repr(value))

    # ── Retrieval ─────────────────────────────────────────────────────────────

    @property
    def entries(self) -> List[LedgerEntry]:
        return list(self._entries)

    @property
    def reversed_entries(self) -> List[LedgerEntry]:
        return list(reversed(self._entries))

    @property
    def root_hash(self) -> bytes:
        return self._prev_hash

    def io_outputs(self) -> List[Any]:
        """Return all values written to stdout during the forward pass,
        in the order they were written."""
        results = []
        for e in self._entries:
            if e.rule == RULE_IO_OUT:
                # term_after holds repr(value); we stored the string version
                results.append(e.term_after)
        return results

    def verify_chain(self) -> bool:
        """Verify the hash chain integrity."""
        prev = b"\x00" * 32
        for entry in self._entries:
            expected = LedgerEntry(
                step_id=entry.step_id,
                rule=entry.rule,
                term_before=entry.term_before,
                term_after=entry.term_after,
                timestamp_ns=entry.timestamp_ns,
                prev_hash=prev,
            ).entry_hash
            if expected != entry.entry_hash:
                return False
            prev = entry.entry_hash
        return True

    def __len__(self) -> int:
        return len(self._entries)

    def __repr__(self) -> str:
        return f"ExecutionLedger({len(self._entries)} entries)"
