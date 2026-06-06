#!/usr/bin/env python3
"""LLM client adapter — OpenAI / Ollama unified interface.

Does NOT modify extract_data.py.  run_extract.py imports this and
injects the right backend before calling extract_data.py internals.
"""

import json
import os
from typing import Optional


class LLMClient:
    """Unified LLM caller that dispatches to OpenAI or Ollama."""

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4.1-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key
        self.base_url = base_url or os.environ.get("OLLAMA_HOST", "http://localhost:11434/v1")
        self._client = None

    def _ensure_client(self):
        if self._client is not None:
            return
        if self.provider == "openai":
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key or os.environ.get("OPENAI_API_KEY"))
        elif self.provider == "ollama":
            from openai import OpenAI
            self._client = OpenAI(
                api_key="ollama",  # placeholder, Ollama ignores it
                base_url=self.base_url,
            )
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def chat(self, system: str, user: str, temperature: float = 0.1, max_tokens: int = 4096) -> str:
        self._ensure_client()
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()

    @property
    def provider_name(self) -> str:
        return self.provider
