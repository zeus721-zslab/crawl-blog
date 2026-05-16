import json
from typing import AsyncIterator

import httpx

from llm.base import LLMProvider, JUDGE_SYSTEM, REFINE_SYSTEM


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def _chat(self, system: str, user: str) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "stream": False,
                },
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]

    async def judge_input(self, value: str) -> dict:
        text = await self._chat(JUDGE_SYSTEM, f"Input: {value}")
        return json.loads(text)

    async def stream_judge(self, value: str) -> AsyncIterator[str]:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": JUDGE_SYSTEM},
                        {"role": "user", "content": f"Input: {value}"},
                    ],
                    "stream": True,
                },
            ) as resp:
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    chunk = data.get("message", {}).get("content", "")
                    if chunk:
                        yield chunk

    async def refine_content(self, raw: str, source_url: str) -> dict:
        text = await self._chat(
            REFINE_SYSTEM,
            f"Source: {source_url}\n\nContent:\n{raw[:8000]}",
        )
        return json.loads(text)
