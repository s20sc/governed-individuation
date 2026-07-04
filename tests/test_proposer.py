"""The proposer builds an action proposal from the task and the realization
layer. The load-bearing design choice (design doc §8): the prompt explicitly
surfaces what was refused before, so the realization layer can actually shift
the proposal distribution — this is what makes the recurrence rate fall.
"""

from aeros.runtime.persona_core import PersonaCore

from gi.proposer import build_proposal_prompt, parse_proposal
from gi.realization import RealizationLayer


def _R():
    return RealizationLayer(PersonaCore())


def test_prompt_includes_task_and_allowed_capabilities():
    ctx = {"task": "stack the red block", "allowed_capabilities": ["pick", "place"]}
    prompt = build_proposal_prompt(ctx, _R())
    assert "stack the red block" in prompt
    assert "pick" in prompt and "place" in prompt


def test_prompt_surfaces_blocked_history():
    ctx = {"task": "t", "allowed_capabilities": ["pick"]}
    layer = _R()
    layer.sediment_block("force_through_obstacle", "red_line")
    prompt = build_proposal_prompt(ctx, layer)
    assert "force_through_obstacle" in prompt  # the proposer is told what was refused


def test_parse_proposal_extracts_json_capability():
    p = parse_proposal('{"capability": "pick", "payload": {"obj": "red"}}')
    assert p.capability == "pick"
    assert p.payload == {"obj": "red"}


def test_parse_proposal_tolerates_surrounding_text():
    p = parse_proposal('Sure, here:\n{"capability": "place", "payload": {}}\nDone.')
    assert p.capability == "place"


def test_parse_proposal_recovers_from_invalid_json_escape():
    # some models emit invalid JSON escapes (e.g. \_); recover the capability anyway
    p = parse_proposal(r'{"capability": "pick\_the\_lock", "payload": {}}')
    assert p.capability == "pick_the_lock"


def test_suppress_arm_omits_blocked_history():
    """The Suppress arm (consult_realization=False) does not surface what was
    refused — the agent is governed but never learns. This is the ablation
    contrast for whether realization-layer feedback is what shifts proposals."""
    ctx = {"task": "t", "allowed_capabilities": ["safe"]}
    layer = _R()
    layer.sediment_block("force_through_obstacle", "red_line")
    prompt = build_proposal_prompt(ctx, layer, consult_realization=False)
    assert "force_through_obstacle" not in prompt
