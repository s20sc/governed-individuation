"""I3 — the individuation trajectory is reconstructible from the cause-linked
audit. Every refusal carries a cause id; every realization-layer event traces
back to exactly one refusal. The audit is complete iff that link is a bijection.
"""

from aeros.runtime.persona_core import PersonaCore

from gi.audit import reconstruction_complete
from gi.loop import Decision, GovernedIndividuationLoop, Proposal
from gi.realization import RealizationLayer


def test_every_refusal_is_cause_linked_to_one_event():
    layer = RealizationLayer(PersonaCore())
    flip = {"n": 0}

    def proposer(ctx, r):
        flip["n"] += 1
        return Proposal("danger" if flip["n"] % 2 else "safe", {})

    loop = GovernedIndividuationLoop(
        layer, lambda cap, ctx: Decision(cap != "danger", "red_line"), proposer
    )
    results = [loop.step({}) for _ in range(10)]

    assert sum(1 for r in results if not r.allowed) == 5
    assert reconstruction_complete(results, layer) is True


def test_orphan_event_breaks_reconstruction():
    layer = RealizationLayer(PersonaCore())
    layer.sediment_block("ghost", reason="orphan-cause")  # an event with no step behind it
    assert reconstruction_complete(results=[], realization=layer) is False
