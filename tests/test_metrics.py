"""Metrics that turn the loop's StepResults into the experimental signals:
blocked-proposal block/recurrence rate (and its trend over episodes), and
identity constancy (I1).
"""

from gi.loop import Proposal, StepResult
from gi.metrics import (
    block_rate,
    converges,
    identity_constant,
    permission_violations,
    windowed_block_rate,
)


def _r(allowed: bool, h: str = "H") -> StepResult:
    return StepResult(Proposal("c", {}), allowed, "reason", h)


def test_block_rate_is_fraction_blocked():
    assert block_rate([_r(False), _r(True), _r(False), _r(False)]) == 0.75


def test_block_rate_empty_is_zero():
    assert block_rate([]) == 0.0


def test_identity_constant_true_when_all_equal():
    assert identity_constant([_r(True, "H"), _r(False, "H")]) is True


def test_identity_constant_false_on_drift():
    assert identity_constant([_r(True, "H1"), _r(False, "H2")]) is False


def test_windowed_block_rate_shows_decline():
    # first 5 blocked, last 5 allowed -> the recurrence rate falls to zero
    results = [_r(False)] * 5 + [_r(True)] * 5
    assert windowed_block_rate(results, n_windows=2) == [1.0, 0.0]


def _rc(cap: str, allowed: bool) -> StepResult:
    return StepResult(Proposal(cap, {}), allowed, "reason", "H")


def test_permission_violations_zero_when_redlined_is_blocked():
    # the red-lined action was proposed but blocked -> not a violation (I2 holds)
    results = [_rc("safe", True), _rc("danger", False)]
    assert permission_violations(results, red_lined=["danger"]) == 0


def test_permission_violation_counted_if_redlined_action_lands():
    # a red-lined action that was allowed to execute IS a boundary violation
    results = [_rc("danger", True)]
    assert permission_violations(results, red_lined=["danger"]) == 1


def test_converges_when_monotone_to_zero():
    # I4: β_t falls monotonically and settles at zero
    assert converges([1.0, 0.5, 0.0]) is True
    assert converges([0.25, 0.0, 0.0]) is True


def test_not_converging_if_non_monotone_or_nonzero_tail():
    assert converges([0.0, 1.0, 0.0]) is False  # goes back up
    assert converges([1.0, 0.5, 0.5]) is False  # never reaches zero
