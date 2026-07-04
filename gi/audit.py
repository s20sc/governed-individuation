"""I3 — auditability of the individuation trajectory.

Every refusal carries a cause id; the realization-layer event it produces is
stamped with that same cause id (in triggering_cause_ids). The audit is complete
iff refusals and events are in one-to-one correspondence: no refusal without a
recorded event, no event without a refusal behind it.
"""

from collections.abc import Sequence

from gi.loop import StepResult
from gi.realization import RealizationLayer


def reconstruction_complete(results: Sequence[StepResult], realization: RealizationLayer) -> bool:
    refusals = [r for r in results if not r.allowed]
    refusal_ids = {r.cause_id for r in refusals}
    event_ids = {
        e.triggering_cause_ids[0] for e in realization.events if e.triggering_cause_ids
    }
    return (
        len(refusal_ids) == len(refusals)  # each refusal has a distinct cause id
        and len(event_ids) == len(realization.events)  # each event traces to a distinct cause
        and refusal_ids == event_ids  # exact one-to-one correspondence
    )
