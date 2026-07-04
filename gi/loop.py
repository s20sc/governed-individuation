"""The Governed Individuation Loop driver.

One step: the proposer suggests an action (shaped by the effective persona that
the realization layer folds), governance permits or refuses it, and a refusal
sediments into the realization layer. The identity digest is read after every
step; it never moves inside the loop.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from gi.realization import RealizationLayer


@dataclass
class Proposal:
    capability: str
    payload: dict[str, Any]


@dataclass
class Decision:
    allowed: bool
    reason: str


@dataclass
class StepResult:
    proposal: Proposal
    allowed: bool
    reason: str
    identity_h: str
    cause_id: str = ""


Proposer = Callable[[dict[str, Any], RealizationLayer], Proposal]
Governance = Callable[[str, dict[str, Any]], Decision]


class GovernedIndividuationLoop:
    def __init__(
        self,
        realization: RealizationLayer,
        governance: Governance,
        proposer: Proposer,
    ) -> None:
        self.realization = realization
        self.governance = governance
        self.proposer = proposer
        self._step = 0

    def step(self, context: dict[str, Any]) -> StepResult:
        cause_id = f"c{self._step}"
        self._step += 1
        proposal = self.proposer(context, self.realization)
        decision = self.governance(proposal.capability, context)
        if not decision.allowed:
            # the cause id links this refusal to the realization-layer event it
            # produces, so the trajectory is reconstructible from the audit (I3).
            self.realization.sediment_block(proposal.capability, reason=cause_id)
        return StepResult(
            proposal=proposal,
            allowed=decision.allowed,
            reason=decision.reason,
            identity_h=self.realization.identity_digest(),
            cause_id=cause_id,
        )
