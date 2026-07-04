"""The Governed Individuation Loop — one step.

propose -> (mediate) -> govern -> execute or sediment. Tested with injected
stub proposer + governance so the loop logic is isolated from the LLM and the
real PolicyEvaluator. Identity must hold across every step.
"""

from aeros.runtime.persona_core import PersonaCore

from gi.loop import Decision, GovernedIndividuationLoop, Proposal
from gi.realization import RealizationLayer


def _loop(proposer, governance):
    return GovernedIndividuationLoop(
        realization=RealizationLayer(PersonaCore(name="r")),
        governance=governance,
        proposer=proposer,
    )


def test_blocked_proposal_sediments_and_identity_holds():
    loop = _loop(
        proposer=lambda ctx, r: Proposal("skill.dangerous", {}),
        governance=lambda cap, ctx: Decision(allowed=False, reason="red_line"),
    )
    h0 = loop.realization.identity_digest()

    result = loop.step(context={"task": "t1"})

    assert result.allowed is False
    assert len(loop.realization) == 1  # blocked proposal sedimented into R
    assert result.identity_h == h0  # identity held across the step


def test_allowed_proposal_does_not_sediment():
    loop = _loop(
        proposer=lambda ctx, r: Proposal("skill.pick", {}),
        governance=lambda cap, ctx: Decision(allowed=True, reason="ok"),
    )

    result = loop.step(context={"task": "t1"})

    assert result.allowed is True
    assert len(loop.realization) == 0  # nothing sedimented on allow


def test_identity_holds_across_many_mixed_steps():
    flip = {"n": 0}

    def proposer(ctx, r):
        flip["n"] += 1
        return Proposal("skill.dangerous" if flip["n"] % 2 else "skill.pick", {})

    loop = _loop(
        proposer=proposer,
        governance=lambda cap, ctx: Decision(
            allowed=(cap != "skill.dangerous"), reason="red_line"
        ),
    )
    h0 = loop.realization.identity_digest()

    results = [loop.step(context={"task": f"t{i}"}) for i in range(10)]

    assert all(r.identity_h == h0 for r in results)  # I1 across the whole run
    assert len(loop.realization) == 5  # the 5 dangerous proposals sedimented
