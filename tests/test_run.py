"""The episode runner: run the loop for N steps on a scenario, collect results
and metrics. Tested with deterministic proposers so the plumbing (governance
blocks the red-lined capability, identity holds, the recurrence rate declines
when the proposer consults the realization layer) is validated without the LLM.
"""

from gi.loop import Proposal
from gi.run import Scenario, run_episodes

SCENARIO = Scenario(
    task="retrieve the object",
    allowed_capabilities=["navigate_around", "force_through"],
    red_lined=["force_through"],
)


def test_red_lined_capability_is_always_blocked():
    run = run_episodes(SCENARIO, proposer=lambda ctx, r: Proposal("force_through", {}), n_steps=10)
    assert run.block_rate == 1.0
    assert run.identity_constant is True
    assert len(run.results) == 10


def test_permitted_capability_is_never_blocked():
    run = run_episodes(SCENARIO, proposer=lambda ctx, r: Proposal("navigate_around", {}), n_steps=8)
    assert run.block_rate == 0.0


def test_recurrence_rate_declines_when_proposer_consults_realization():
    def learner(ctx, realization):
        blocked = {e.capability for e in realization.events}
        cap = "navigate_around" if "force_through" in blocked else "force_through"
        return Proposal(cap, {})

    run = run_episodes(SCENARIO, proposer=learner, n_steps=10, n_windows=2)
    assert run.windowed_block_rate[0] > run.windowed_block_rate[-1]
    assert run.identity_constant is True
