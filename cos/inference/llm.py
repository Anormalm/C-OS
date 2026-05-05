from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol
from urllib import error, request


class JSONLLMClient(Protocol):
    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
        ...


@dataclass
class DeepSeekClient:
    api_key: str
    model: str = "deepseek-v4-pro"
    base_url: str = "https://api.deepseek.com"
    timeout_seconds: float = 20.0
    reasoning_effort: str = "high"

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
        endpoint = f"{self.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "reasoning_effort": self.reasoning_effort,
            "thinking": {"type": "enabled"},
            "response_format": {"type": "json_object"},
            "stream": False,
        }
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        req = request.Request(endpoint, data=body, method="POST", headers=headers)
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
        except (error.URLError, TimeoutError, ValueError):
            return None

        try:
            data = json.loads(raw)
            content = data["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                return None
            return self._parse_json_string(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError):
            return None

    @staticmethod
    def _parse_json_string(content: str) -> dict[str, Any] | None:
        text = content.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()
        first = text.find("{")
        last = text.rfind("}")
        if first == -1 or last == -1 or last <= first:
            return None
        blob = text[first : last + 1]
        try:
            parsed = json.loads(blob)
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed, dict):
            return None
        return parsed
