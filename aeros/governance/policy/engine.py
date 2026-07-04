"""Policy engine: three-layer permission check for skill execution."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SystemPolicy:
    """Immutable system-wide policy constraints."""

    allowed_actuators: tuple[str, ...] = ("arm", "gripper", "camera", "base")
    blocked_risk_levels: tuple[str, ...] = ("high", "critical")


@dataclass(frozen=True)
class PermissionResult:
    """Immutable result of a permission check."""

    allowed: bool
    reason: str | None = None


@dataclass
class PolicyEngine:
    """Three-layer policy engine: operator override → ECM scope → system risk."""

    _system_policy: SystemPolicy = field(default_factory=SystemPolicy)
    _blocked_skills: set[str] = field(default_factory=set)

    def __init__(self, system_policy: SystemPolicy | None = None) -> None:
        """Initialize with optional custom system policy."""
        self._system_policy = system_policy or SystemPolicy()
        self._blocked_skills: set[str] = set()

    def block_skill(self, name: str) -> None:
        """Add a skill to the operator-level block list."""
        self._blocked_skills.add(name)
        logger.info("Skill blocked by operator: %s", name)

    def unblock_skill(self, name: str) -> None:
        """Remove a skill from the operator-level block list."""
        self._blocked_skills.discard(name)
        logger.info("Skill unblocked by operator: %s", name)

    def check_permission(
        self, skill_name: str, ecm_id: str, ecm_permissions: dict[str, Any]
    ) -> PermissionResult:
        """Run three-layer permission check.

        Layer 1: operator override (_blocked_skills set).
        Layer 2: ECM-declared allowed_skills.
        Layer 3: skill-level risk + actuator scope vs SYSTEM_POLICY.
        """
        # Layer 1: operator override
        if skill_name in self._blocked_skills:
            reason = f"skill '{skill_name}' is blocked by operator"
            logger.debug("DENY (L1): %s / %s — %s", skill_name, ecm_id, reason)
            return PermissionResult(allowed=False, reason=reason)

        # Layer 2: ECM-declared allowed_skills
        allowed_skills: list[str] | None = ecm_permissions.get("allowed_skills")
        if allowed_skills is not None and skill_name not in allowed_skills:
            reason = f"skill '{skill_name}' not in ECM '{ecm_id}' allowed_skills"
            logger.debug("DENY (L2): %s / %s — %s", skill_name, ecm_id, reason)
            return PermissionResult(allowed=False, reason=reason)

        # Layer 3: skill-level risk + actuator scope vs system policy
        skill_risk: str | None = ecm_permissions.get("risk_level")
        if skill_risk is not None and skill_risk in self._system_policy.blocked_risk_levels:
            reason = f"skill '{skill_name}' risk level '{skill_risk}' is blocked by system policy"
            logger.debug("DENY (L3-risk): %s / %s — %s", skill_name, ecm_id, reason)
            return PermissionResult(allowed=False, reason=reason)

        skill_actuators: list[str] = ecm_permissions.get("actuators", [])
        unauthorized = [
            a for a in skill_actuators if a not in self._system_policy.allowed_actuators
        ]
        if unauthorized:
            reason = f"skill '{skill_name}' requires unauthorized actuators: {unauthorized}"
            logger.debug("DENY (L3-actuator): %s / %s — %s", skill_name, ecm_id, reason)
            return PermissionResult(allowed=False, reason=reason)

        logger.debug("ALLOW: %s / %s", skill_name, ecm_id)
        return PermissionResult(allowed=True)
