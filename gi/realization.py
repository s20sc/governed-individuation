"""The realization layer R — sediments blocked proposals as adaptive events.

R wraps the frozen seed (PersonaCore) and an append-only list of
PersonaAdaptiveEvents. Blocked proposals sediment as auto-tighten events, which
require no operator signature: autonomous growth can only make the agent more
careful, never widen what it may do (the asymmetric-trust rule). The seed is
never touched, so the identity digest H is invariant as R grows.
"""

from datetime import datetime, timezone

UTC = timezone.utc

from aeros.runtime.persona_core import PersonaCore
from aeros.runtime.persona_event import PersonaAdaptiveEvent

from gi.identity import identity_digest

_DEFAULT_CONFIDENCE_STEP = 0.05


class RealizationLayer:
    def __init__(self, core: PersonaCore) -> None:
        self.core = core
        self.events: list[PersonaAdaptiveEvent] = []

    def sediment_block(
        self,
        capability: str,
        reason: str,
        magnitude: float = _DEFAULT_CONFIDENCE_STEP,
    ) -> PersonaAdaptiveEvent:
        """Record a blocked proposal as an auto-tighten (unsigned) event."""
        event = PersonaAdaptiveEvent(
            kind="skill_confidence_decrease",
            capability=capability,
            delta={"magnitude": magnitude},
            triggering_cause_ids=(reason,),
            timestamp=datetime.now(UTC),
        )
        self.events.append(event)
        return event

    def identity_digest(self) -> str:
        """H over the frozen seed — invariant regardless of how R grows."""
        return identity_digest(self.core)

    def __len__(self) -> int:
        return len(self.events)
