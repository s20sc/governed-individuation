"""I1 integration — identity invariance while the realization layer grows.

The realization layer R sediments blocked proposals as auto-tighten adaptive
events. As R grows, the effective persona adapts, but the identity digest H
(a function of the frozen seed alone) must not move.
"""

from aeros.runtime.persona_core import PersonaCore

from gi.identity import identity_digest
from gi.realization import RealizationLayer


def test_identity_invariant_as_realization_layer_grows():
    core = PersonaCore(name="robot-a", description="warehouse picker")
    h0 = identity_digest(core)
    layer = RealizationLayer(core)

    for i in range(20):
        layer.sediment_block(capability=f"skill.pick_{i % 3}", reason="policy_block")

    assert len(layer) == 20  # the realization layer grew
    assert layer.identity_digest() == h0  # ... but identity H did not move
    assert identity_digest(core) == h0  # core itself untouched


def test_sedimented_events_are_auto_tighten_unsigned():
    """Blocks sediment as auto-tighten events: no operator signature required."""
    from aeros.runtime.persona_event import is_automatic_tighten_kind

    layer = RealizationLayer(PersonaCore())
    layer.sediment_block(capability="skill.pick", reason="policy_block")

    event = layer.events[0]
    assert is_automatic_tighten_kind(event.kind)
    assert event.operator_signature is None
