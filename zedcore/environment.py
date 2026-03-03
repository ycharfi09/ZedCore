"""Variable environment (scope chain) for ZedCore."""

from __future__ import annotations

from typing import Any, Dict, Optional


class Environment:
    """A lexically-scoped variable environment.

    Each `Environment` has an optional parent; variable lookup walks up the
    chain until a binding is found (or raises NameError).
    """

    def __init__(self, parent: Optional["Environment"] = None) -> None:
        self._bindings: Dict[str, Any] = {}
        self.parent = parent

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def define(self, name: str, value: Any) -> None:
        """Bind *name* in the current (innermost) scope."""
        self._bindings[name] = value

    def set(self, name: str, value: Any) -> None:
        """Update an existing binding anywhere in the scope chain.

        If the name is not found, creates a new binding in the current scope.
        """
        env: Optional["Environment"] = self
        while env is not None:
            if name in env._bindings:
                env._bindings[name] = value
                return
            env = env.parent
        self._bindings[name] = value

    def get(self, name: str) -> Any:
        """Look up *name* in the scope chain."""
        env: Optional["Environment"] = self
        while env is not None:
            if name in env._bindings:
                return env._bindings[name]
            env = env.parent
        raise NameError(f"Undefined variable: {name!r}")

    def has(self, name: str) -> bool:
        env: Optional["Environment"] = self
        while env is not None:
            if name in env._bindings:
                return True
            env = env.parent
        return False

    def child(self) -> "Environment":
        """Create a child scope."""
        return Environment(parent=self)

    def snapshot(self) -> Dict[str, Any]:
        """Return a shallow copy of the current scope's bindings."""
        return dict(self._bindings)

    def __repr__(self) -> str:
        keys = list(self._bindings.keys())
        return f"Environment({keys!r})"
