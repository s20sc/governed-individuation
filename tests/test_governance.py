"""The governance G — real aeros PolicyEngine wrapped as a loop Governance.

block_skill defines the frozen red-lines (the permission boundary). The unsafe
capability is blocked and stays blocked regardless of what the proposer asks —
the I2 substrate.
"""

from gi.governance import AerosGovernance
from gi.loop import Decision


def _ctx(allowed_skills=None, risk="low", actuators=("arm",)):
    return {"permissions": {"allowed_skills": allowed_skills, "risk_level": risk, "actuators": list(actuators)}}


def test_operator_blocked_skill_is_denied():
    gov = AerosGovernance(blocked_skills=["dangerous"])
    d = gov("dangerous", _ctx(allowed_skills=["dangerous"]))
    assert isinstance(d, Decision)
    assert d.allowed is False
    assert "blocked" in d.reason


def test_high_risk_skill_is_denied():
    gov = AerosGovernance()
    d = gov("grasp", _ctx(allowed_skills=["grasp"], risk="high"))
    assert d.allowed is False


def test_permitted_skill_is_allowed():
    gov = AerosGovernance()
    d = gov("grasp", _ctx(allowed_skills=["grasp"]))
    assert d.allowed is True


def test_blocked_set_is_the_permission_boundary():
    """A blocked skill is denied even when the ECM would otherwise allow it."""
    gov = AerosGovernance(blocked_skills=["dangerous"])
    d = gov("dangerous", _ctx(allowed_skills=["dangerous", "grasp"], risk="low"))
    assert d.allowed is False
