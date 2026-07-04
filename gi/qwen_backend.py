"""Local Qwen text-generation backend (transformers, greedy decoding).

Greedy (do_sample=False) makes the proposal deterministic given the prompt, so
any change in the agent's proposals is attributable to the prompt — i.e. to the
realization-layer feedback — not to sampling noise.
"""

from __future__ import annotations

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


class QwenBackend:
    def __init__(
        self, model_path: str, max_new_tokens: int = 96, temperature: float = 0.0
    ) -> None:
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = (
            AutoModelForCausalLM.from_pretrained(
                model_path, torch_dtype=torch.bfloat16, device_map="cuda"
            )
            .eval()
        )
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature

    def seed(self, value: int) -> None:
        """Seed the decoding RNG. Call once at the start of a run so a GI and a
        Suppress arm share the same sampling randomness (a fair paired run)."""
        torch.manual_seed(value)

    @torch.no_grad()
    def generate(self, prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(text, return_tensors="pt").to(self.model.device)
        do_sample = self.temperature > 0
        out = self.model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            do_sample=do_sample,
            temperature=self.temperature if do_sample else None,
            top_p=0.9 if do_sample else None,
            pad_token_id=self.tokenizer.eos_token_id,
        )
        generated = out[0][inputs.input_ids.shape[1] :]
        return self.tokenizer.decode(generated, skip_special_tokens=True)
