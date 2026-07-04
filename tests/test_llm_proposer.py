"""LLMProposer wires a text-generation backend into the loop. Tested with a
fake backend so the wiring (prompt in, parsed Proposal out, and crucially the
realization-layer feedback reaching the prompt) is verified without the model.
"""

from aeros.runtime.persona_core import PersonaCore

from gi.proposer import LLMProposer
from gi.realization import RealizationLayer


class FakeBackend:
    def __init__(self, response: str) -> None:
        self.response = response
        self.last_prompt: str | None = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response


def test_llm_proposer_parses_backend_output():
    proposer = LLMProposer(FakeBackend('{"capability": "pick", "payload": {}}'))
    p = proposer({"task": "t", "allowed_capabilities": ["pick"]}, RealizationLayer(PersonaCore()))
    assert p.capability == "pick"


def test_llm_proposer_feeds_blocked_history_to_backend():
    backend = FakeBackend('{"capability": "safe", "payload": {}}')
    proposer = LLMProposer(backend)
    layer = RealizationLayer(PersonaCore())
    layer.sediment_block("force_through", "red_line")

    proposer({"task": "t", "allowed_capabilities": ["safe"]}, layer)

    assert "force_through" in backend.last_prompt  # R-feedback reached the model


def test_suppress_arm_proposer_withholds_blocked_history():
    backend = FakeBackend('{"capability": "safe", "payload": {}}')
    proposer = LLMProposer(backend, consult_realization=False)
    layer = RealizationLayer(PersonaCore())
    layer.sediment_block("force_through", "red_line")

    proposer({"task": "t", "allowed_capabilities": ["safe"]}, layer)

    assert "force_through" not in backend.last_prompt  # Suppress: agent never learns
