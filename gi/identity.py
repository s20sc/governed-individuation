"""I1: the identity digest H — a pure function of the frozen seed S."""

import hashlib
import json

from aeros.runtime.persona_core import PersonaCore


def identity_digest(core: PersonaCore) -> str:
    """SHA-256 over the canonical manifest of the frozen seed.

    The digest is the agent's verifiable identity H. It is a function of the
    PersonaCore (the seed S) alone; the realization layer and the effective
    persona never enter the computation. Anyone holding the reference manifest
    can recompute and check it.
    """
    payload = core.to_manifest_payload()
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
