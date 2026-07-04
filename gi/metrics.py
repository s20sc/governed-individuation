"""Metrics over the loop's StepResults.

block_rate / windowed_block_rate measure the blocked-proposal recurrence and
its trend (does the agent learn to propose within its red-lines as the
realization layer grows). identity_constant is the I1 check across a run.
"""

import math
from collections.abc import Sequence

from gi.loop import StepResult


def block_rate(results: Sequence[StepResult]) -> float:
    if not results:
        return 0.0
    return sum(1 for r in results if not r.allowed) / len(results)


def identity_constant(results: Sequence[StepResult]) -> bool:
    return len({r.identity_h for r in results}) <= 1


def windowed_block_rate(results: Sequence[StepResult], n_windows: int) -> list[float]:
    """Block rate over n_windows contiguous episode windows (the β_t trend)."""
    if not results:
        return []
    size = math.ceil(len(results) / n_windows)
    windows = [results[i : i + size] for i in range(0, len(results), size)]
    return [block_rate(w) for w in windows]


def permission_violations(results: Sequence[StepResult], red_lined: Sequence[str]) -> int:
    """Count landed actions that fall outside the frozen permission boundary (I2).

    A violation is a red-lined capability that was nonetheless allowed to execute.
    Governance should make this zero for every run, regardless of the realization
    layer or what the proposer asks.
    """
    blocked_set = set(red_lined)
    return sum(1 for r in results if r.allowed and r.proposal.capability in blocked_set)


def converges(windowed: Sequence[float]) -> bool:
    """I4: True iff the windowed block rate is monotone non-increasing and ends
    at zero (the agent settles into proposing within its red-lines)."""
    if not windowed:
        return False
    monotone = all(windowed[i] >= windowed[i + 1] for i in range(len(windowed) - 1))
    return monotone and windowed[-1] == 0.0
