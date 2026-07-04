"""The inducer — abstracts the realization layer's refusals into a natural-language
governance principle, so the agent generalizes from its OWN refusal history rather
than from an author-written rule.

This closes the "injected abstraction" gap flagged in review: in the
earlier transfer pilot the generalizing principle was hand-written, so a skeptic could
say the author supplied the abstraction. Here the principle that drives held-out
generalization is produced BY THE SYSTEM from the (situation, refused-action) pairs it
accumulated during training. The induced principle then enters only the proposer
(downstream of the frozen governance gate), so even a wrong induction can over-block
but never widen the permission boundary.
"""

from typing import Any


def build_induction_prompt(refusals: list[tuple[str, str]]) -> str:
    """refusals: list of (situation/task, refused capability name)."""
    lines = [
        "A governance layer refused the following proposed robot actions. "
        "Each line gives the situation and the action that was refused in it:",
    ]
    for task, action in refusals:
        lines.append(f"- Situation: {task}")
        lines.append(f"  Refused action: {action}")
    lines.append(
        "In ONE sentence, state the general principle that explains why these actions "
        "were refused, phrased so it can be applied to NEW situations that are not listed "
        "above. Begin the sentence with the word 'Avoid'."
    )
    return "\n".join(lines)


def induce_principle(backend: Any, refusals: list[tuple[str, str]]) -> str:
    """Ask the model to abstract the refusal history into a one-sentence principle."""
    text = backend.generate(build_induction_prompt(refusals))
    # Keep the first non-empty line; strip list markers / quotes the model may add.
    for line in text.strip().splitlines():
        line = line.strip().lstrip("-*0123456789. ").strip().strip('"').strip()
        if line:
            return line
    return text.strip()
