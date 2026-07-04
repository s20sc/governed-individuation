"""Persistent Agent A = (π_A, M_A^id, M_A^ep) — identity invariance.

The central claim is that capability evolution should never alter the
agent's identity: the policy π_A and identity memory M_A^id are FROZEN, while
only the episodic memory M_A^ep grows. The drift metric Δπ is then a hard
zero by construction — capability upgrades demonstrably preserve identity.

In the full runtime this manifests as a small PyTorch policy network
that's literally `requires_grad=False`. AEROS's "agent" is a composite of
the (external) LLM runtime plus the bridge's frozen configuration, so
the aeros-native equivalent freezes a *manifest* of:

    π_A      = the planner system prompt + tool definitions
    M_A^id   = env_policies + policy.yaml + ECM contract hashes

Capability evolution changes ECM *versions* — that's by design.
The identity hash only includes the ECM **registry shape** (which capabilities
exist), not which version is installed. A safe upgrade leaves identity
intact; an unsafe one (renamed capability, removed safety constraint) will
flip the hash and the persistent-agent contract will detect it.

This module is intentionally side-effect-free: it produces hashes and
manages the episodic ring buffer; wiring into bridge lifespan happens in
separate signed transitions.
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aeros.runtime.episodic_db import EpisodicStore

logger = logging.getLogger(__name__)


def _stable_hash(payload: object) -> str:
    """Deterministic SHA-256 over a JSON-serialised payload.

    Sorting keys at every level so two semantically-equal manifests hash to
    the same digest regardless of input dict insertion order.
    """
    text = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class IdentityManifest:
    """Frozen record of everything that defines "who this agent is".

    Never construct one mutably — every write should produce a new manifest
    via dataclass replace(). PersistentAgent.compute_identity_drift() compares
    the active manifest's hash to the original snapshot.

    `persona_hash` was added in phase F to fold the PersonaProfile (the
    "soul" layer) into identity. Editing persona.yaml flips the hash;
    same-name ECM version upgrades still don't.
    """

    system_prompt: str
    env_policies_hash: str
    policy_rules_hash: str
    ecm_registry_hash: str
    persona_hash: str = ""  # phase F: empty string means "no persona layer"
    runtime_version: str = "0.5.0"
    schema_version: str = "v1"

    @property
    def identity_hash(self) -> str:
        """SHA-256 over the full frozen manifest. The paper-claim invariant."""
        return _stable_hash(
            {
                "system_prompt": self.system_prompt,
                "env_policies_hash": self.env_policies_hash,
                "policy_rules_hash": self.policy_rules_hash,
                "ecm_registry_hash": self.ecm_registry_hash,
                "persona_hash": self.persona_hash,
                "runtime_version": self.runtime_version,
                "schema_version": self.schema_version,
            },
        )


def hash_env_policies(policies: dict[str, object]) -> str:
    """Hash a serialised env_policies snapshot. Stable across dict orderings."""
    return _stable_hash(policies)


def hash_policy_rules(rules: list[dict[str, object]] | tuple[dict[str, object], ...]) -> str:
    """Hash the policy.yaml rule list. Order-sensitive (rule order matters)."""
    return _stable_hash([dict(rule) for rule in rules])


def hash_ecm_registry(registered_capabilities: list[str] | tuple[str, ...]) -> str:
    """Hash the *shape* of the ECM registry — capability names only.

    Versions deliberately excluded: the invariance and evolution results require the agent's
    identity to survive ECM version evolution, but to flip the moment a
    capability is renamed, removed, or added.
    """
    return _stable_hash(sorted(set(registered_capabilities)))


def hash_persona(persona_payload: dict[str, object]) -> str:
    """Hash a PersonaProfile.to_manifest_payload() dict.

    Editing persona.yaml flips identity (intentional — the
    robot's "soul" is part of who it is). Pass an empty dict to
    represent "no persona layer", which yields a stable, distinct hash.
    """
    return _stable_hash(persona_payload)


@dataclass(frozen=True)
class EpisodicRecord:
    """A single immutable entry in the episodic memory M_A^ep."""

    timestamp: str
    kind: str  # 'intent', 'decision', 'execution', 'override' …
    intent_id: str | None
    summary: str
    payload: dict[str, Any] = field(default_factory=dict)


class EpisodicMemory:
    """Bounded append-only ring buffer of episodic records.

    Bounded so a long-lived bridge process doesn't grow without limit.
    `recent(n)` returns a snapshot tuple safe to read from another thread.

    Layer 1 (RFC §4): pass `db_path` to back the buffer with a
    SQLite file partitioned by `identity_hash`. Bridge restarts then
    recover the previous run's records via `recent(n)`. With `db_path=None`
    (the default — used by tests) the buffer falls back to an in-process
    list with the historical FIFO eviction.
    """

    def __init__(
        self,
        capacity: int = 1000,
        *,
        db_path: Path | None = None,
        identity_hash: str = "",
    ) -> None:
        if capacity < 1:
            raise ValueError(f"capacity must be >= 1, got {capacity}")
        self._capacity = capacity
        self._identity_hash = identity_hash
        self._db_path = db_path
        self._records: list[EpisodicRecord] = []
        self._store: EpisodicStore | None = (
            EpisodicStore(db_path) if db_path is not None else None
        )
        # append() does check-then-del to enforce capacity; recent()
        # iterates _records. Concurrent threads can observe truncated state
        # mid-del, or two appends can race the eviction. The same hazard
        # exists for the SQLite path (append + prune is two SQL statements).
        # A single per-instance lock serialises all of it; contention is
        # bounded by sqlite_busy_timeout / GIL latency, which dwarfs the
        # write cost itself.
        self._mutation_lock = threading.Lock()

    def append(self, record: EpisodicRecord) -> None:
        with self._mutation_lock:
            if self._store is not None:
                self._store.append(
                    self._identity_hash,
                    timestamp=record.timestamp,
                    kind=record.kind,
                    intent_id=record.intent_id,
                    summary=record.summary,
                    payload=record.payload,
                )
                self._store.prune_to_capacity(self._identity_hash, self._capacity)
                return
            self._records.append(record)
            if len(self._records) > self._capacity:
                # Drop oldest. There is no formal LRU policy; FIFO is fine
                # because identity is preserved regardless of which records we keep.
                del self._records[: len(self._records) - self._capacity]

    def recent(self, n: int = 10) -> tuple[EpisodicRecord, ...]:
        if n <= 0:
            return ()
        with self._mutation_lock:
            if self._store is not None:
                rows = self._store.recent(self._identity_hash, n)
                return tuple(
                    EpisodicRecord(
                        timestamp=ts,
                        kind=kind,
                        intent_id=intent_id,
                        summary=summary,
                        payload=payload,
                    )
                    for (ts, kind, intent_id, summary, payload) in rows
                )
            return tuple(self._records[-n:])

    def by_kind(self, kind: str) -> tuple[EpisodicRecord, ...]:
        """Return all records matching ``kind`` for this identity, oldest-first.

        Layer 3: ``/api/evolution/audit`` calls this with
        ``kind="migration_import"`` to surface cross-deployment audit-chain
        markers (Belief 5: audit gaps must be visible, not silenced).
        Both backends are scanned the same way; in-memory falls back to a
        Python comprehension which is O(N) — fine, as the in-memory
        backend is bounded by the FIFO capacity.
        """
        with self._mutation_lock:
            if self._store is not None:
                rows = self._store.by_kind(self._identity_hash, kind)
                return tuple(
                    EpisodicRecord(
                        timestamp=ts,
                        kind=row_kind,
                        intent_id=intent_id,
                        summary=summary,
                        payload=payload,
                    )
                    for (ts, row_kind, intent_id, summary, payload) in rows
                )
            return tuple(r for r in self._records if r.kind == kind)

    def __len__(self) -> int:
        with self._mutation_lock:
            if self._store is not None:
                return self._store.count(self._identity_hash)
            return len(self._records)

    @property
    def store(self) -> EpisodicStore | None:
        """Underlying SQLite-backed store, or None for in-memory fallback.

        Layer 2 (`SemanticConsolidator`) needs direct connection access
        to fold episodic rows into `semantic_facts`. Exposing the store
        via a public property keeps that wiring explicit instead of
        callers reaching through ``_store``.
        """
        return self._store

    def close(self) -> None:
        """Release the underlying SQLite connection if one was opened.

        No-op for the in-memory backend. Idempotent.
        """
        if self._store is not None:
            self._store.close()
            self._store = None


class PersistentAgent:
    """A = (π_A, M_A^id, M_A^ep) — identity-invariant agent shell.

    Composes the frozen IdentityManifest with the growing EpisodicMemory,
    and exposes the identity-invariance proof via `identity_drift()` which
    must always return 0.0 by construction. Any non-zero result signals an
    integrity bug — a callsite mutated the manifest in place.
    """

    def __init__(
        self,
        manifest: IdentityManifest,
        episodic_capacity: int = 1000,
        *,
        episodic_db: Path | None = None,
    ) -> None:
        self._initial_manifest = manifest
        self._initial_hash = manifest.identity_hash
        self._current_manifest = manifest
        # Partition the SQLite store by identity_hash so multiple agents
        # backed by the same DB file never see each other's records.
        self._episodic = EpisodicMemory(
            capacity=episodic_capacity,
            db_path=episodic_db,
            identity_hash=self._initial_hash,
        )
        # callable invoked once per record() right after the
        # episodic insert commits. Layer 2 (SemanticConsolidator) attaches
        # itself here so the 100-event threshold trigger fires from
        # ordinary writes without coupling PersistentAgent to the
        # consolidator type. Hook signature is `() -> None` — the
        # consumer captures whatever state it needs in a closure.
        self._post_record_hook: Callable[[], None] | None = None

    def attach_post_record_hook(self, hook: Callable[[], None] | None) -> None:
        """Install (or clear) a post-record callback.

        Called from `record()` AFTER the episodic append has committed,
        OUTSIDE the EpisodicMemory mutation lock. Exceptions raised by
        the hook are caught + logged so a faulty consumer never poisons
        the bridge's write path. Pass `None` to detach. Idempotent.
        """
        self._post_record_hook = hook

    def close(self) -> None:
        """Release any persistent resources (SQLite connection). Idempotent."""
        self._episodic.close()

    @property
    def manifest(self) -> IdentityManifest:
        return self._current_manifest

    @property
    def identity_hash(self) -> str:
        return self._current_manifest.identity_hash

    @property
    def episodic(self) -> EpisodicMemory:
        return self._episodic

    def record(
        self,
        kind: str,
        *,
        intent_id: str | None = None,
        summary: str = "",
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Append a single episodic record. Identity is unaffected by design."""
        self._episodic.append(
            EpisodicRecord(
                timestamp=datetime.now(UTC).isoformat(),
                kind=kind,
                intent_id=intent_id,
                summary=summary,
                payload=dict(payload) if payload else {},
            ),
        )
        hook = self._post_record_hook
        if hook is not None:
            try:
                hook()
            except Exception:  # noqa: BLE001 — write path must not fail on layer-2 fault
                logger.exception("PersistentAgent post-record hook raised; continuing")

    def identity_drift(self) -> float:
        """Δπ — the identity-invariance metric. Returns 0.0 unless manifest was tampered with.

        Implemented as a discrete measure: 0 when hashes match, 1 when they
        differ. An alternative metric is a continuous L2 over policy network params;
        here it's qualitative because aeros's "policy" is an LLM prompt, not
        a parametric net. The contract is the same: zero means identity
        preserved, non-zero means a programmer error mutated state we
        promised to freeze.
        """
        return 0.0 if self._current_manifest.identity_hash == self._initial_hash else 1.0

    def assert_identity_preserved(self) -> None:
        """Hard-stop check; raise if identity drifted. Useful at episode boundaries."""
        if self.identity_drift() != 0.0:
            raise RuntimeError(
                "PersistentAgent identity drift detected: "
                f"initial={self._initial_hash} current={self._current_manifest.identity_hash}",
            )
