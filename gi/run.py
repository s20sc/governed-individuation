"""Episode runner — run the Governed Individuation Loop on a scenario.

A scenario fixes the task, the capabilities the agent may consider, and which
of them are red-lined (blocked by governance). The runner drives N steps and
returns the per-step results plus the headline metrics.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from aeros.runtime.persona_core import PersonaCore

from gi.governance import AerosGovernance
from gi.loop import GovernedIndividuationLoop, Proposal, StepResult
from gi.metrics import (
    block_rate,
    identity_constant,
    permission_violations,
    windowed_block_rate,
)
from gi.realization import RealizationLayer


@dataclass
class Scenario:
    task: str
    allowed_capabilities: list[str]
    red_lined: list[str]


@dataclass
class EpisodeRun:
    results: list[StepResult]
    block_rate: float
    windowed_block_rate: list[float]
    identity_constant: bool
    realization_size: int
    permission_violations: int


Proposer = Callable[[dict[str, Any], RealizationLayer], Proposal]


def run_episodes(
    scenario: Scenario,
    proposer: Proposer,
    n_steps: int,
    n_windows: int = 5,
    seed_name: str = "agent",
) -> EpisodeRun:
    core = PersonaCore(name=seed_name)
    realization = RealizationLayer(core)
    governance = AerosGovernance(blocked_skills=scenario.red_lined)
    loop = GovernedIndividuationLoop(realization, governance, proposer)

    context = {
        "task": scenario.task,
        "allowed_capabilities": scenario.allowed_capabilities,
        "permissions": {"allowed_skills": None, "risk_level": "low", "actuators": []},
    }
    results = [loop.step(context) for _ in range(n_steps)]

    return EpisodeRun(
        results=results,
        block_rate=block_rate(results),
        windowed_block_rate=windowed_block_rate(results, n_windows),
        identity_constant=identity_constant(results),
        realization_size=len(realization),
        permission_violations=permission_violations(results, scenario.red_lined),
    )
