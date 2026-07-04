"""The governance G — the real aeros PolicyEngine as a loop Governance callable.

The set of blocked skills is the frozen red-line boundary. check_permission is
the real four-layer admission gate (operator block, ECM allowed-skills, risk
level, actuators). A blocked capability is refused regardless of what the
proposer asks, which is the substrate for permission-boundary conservation.
"""

from collections.abc import Iterable
from typing import Any

from aeros.governance import PolicyEngine

from gi.loop import Decision

_DEFAULT_PERMISSIONS: dict[str, Any] = {
    "allowed_skills": None,
    "risk_level": "low",
    "actuators": [],
}


class AerosGovernance:
    def __init__(self, blocked_skills: Iterable[str] = ()) -> None:
        self.engine = PolicyEngine()
        for skill in blocked_skills:
            self.engine.block_skill(skill)

    def __call__(self, capability: str, context: dict[str, Any]) -> Decision:
        permissions = context.get("permissions", _DEFAULT_PERMISSIONS)
        ecm_id = context.get("ecm_id", "ecm")
        result = self.engine.check_permission(capability, ecm_id, permissions)
        return Decision(allowed=result.allowed, reason=result.reason or "ok")
