import json
from typing import AsyncIterator

try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None  # type: ignore

from llm.base import LLMProvider, JUDGE_SYSTEM, REFINE_SYSTEM


class GroqProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        if AsyncGroq is None:
            raise ImportError("groq package required: pip install groq")
        self._client = AsyncGroq(api_key=api_key)
        self._model = model

    async def _chat(self, system: str, user: str, max_tokens: int = 2048) -> str:
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content

    async def judge_input(self, value: str) -> dict:
        text = await self._chat(JUDGE_SYSTEM, f"Input: {value}", max_tokens=512)
        return json.loads(text)

    async def stream_judge(self, value: str) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM},
                {"role": "user", "content": f"Input: {value}"},
            ],
            max_tokens=512,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def refine_content(self, raw: str, source_url: str) -> dict:
        text = await self._chat(
            REFINE_SYSTEM,
            f"Source: {source_url}\n\nContent:\n{raw[:8000]}",
        )
        return json.loads(text)
