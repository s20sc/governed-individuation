"""I1 (identity invariance) — unit level.

The identity digest H is a pure function of the frozen seed (PersonaCore).
These tests pin the harness's H computation before we use it as the loop
invariant in the integration tests.
"""

from aeros.runtime.persona_core import PersonaCore

from gi.identity import identity_digest


def test_identity_digest_is_deterministic():
    core = PersonaCore(name="robot-a", description="warehouse picker")
    assert identity_digest(core) == identity_digest(core)


def test_identity_digest_changes_with_seed():
    a = PersonaCore(name="robot-a")
    b = PersonaCore(name="robot-b")
    assert identity_digest(a) != identity_digest(b)


def test_identity_digest_is_sha256_hex():
    h = identity_digest(PersonaCore())
    assert len(h) == 64
    int(h, 16)  # raises if not valid hex
