"""Cancellation primitives for screenshot capture.

Replaces the global ``cancellation_contexts`` TTLCache with a small,
typed abstraction that can be reused across capture paths.

Milestone B: behaviour is kept identical to the previous implementation
(keyed by request_id, TTL of 2x max batch timeout, and boolean
"cancelled" flag), but the state is owned by a dedicated class.
"""

from __future__ import annotations

from typing import Dict, Optional

from cachetools import TTLCache


class CancellationToken:
    """Represents cancellation state for a single capture request."""

    __slots__ = ("_cancelled",)

    def __init__(self) -> None:
        self._cancelled: bool = False

    def cancel(self) -> None:
        """Mark this token as cancelled."""

        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        """Return True if cancellation has been requested."""

        return self._cancelled


class CancellationRegistry:
    """Manages cancellation tokens for in-flight capture requests.

    This is a drop-in replacement for the previous ``cancellation_contexts``
    TTLCache which stored ``{"cancelled": bool}`` dictionaries. We keep the
    same semantics (TTL, maxsize) but expose a small typed API.
    """

    def __init__(self, ttl: int, maxsize: int = 1000) -> None:
        self._tokens: TTLCache[str, CancellationToken] = TTLCache(
            maxsize=maxsize,
            ttl=ttl,
        )

    # --- CRUD operations -------------------------------------------------

    def create(self, request_id: str) -> CancellationToken:
        """Create and register a token for the given request_id."""

        token = CancellationToken()
        self._tokens[request_id] = token
        return token

    def get(self, request_id: str) -> Optional[CancellationToken]:
        """Return the token for ``request_id`` if it exists and is not expired."""

        return self._tokens.get(request_id)

    def remove(self, request_id: str) -> None:
        """Remove the token for ``request_id`` if it exists."""

        self._tokens.pop(request_id, None)

    # --- Cancellation operations ----------------------------------------

    def cancel(self, request_id: str) -> bool:
        """Request cancellation for a single request.

        Returns True if a token existed and has been marked as cancelled.
        """

        token = self._tokens.get(request_id)
        if token is None:
            return False
        token.cancel()
        return True

    def cancel_all(self) -> int:
        """Request cancellation for all active requests.

        Returns the number of tokens that were marked as cancelled.
        """

        count = 0
        for token in list(self._tokens.values()):
            token.cancel()
            count += 1
        return count

    # --- Introspection ---------------------------------------------------

    def is_cancelled(self, request_id: str) -> bool:
        """Return True if the given request has been cancelled."""

        token = self._tokens.get(request_id)
        return bool(token and token.is_cancelled)

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._tokens)


__all__ = ["CancellationToken", "CancellationRegistry"]

