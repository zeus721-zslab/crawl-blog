import json
from typing import AsyncIterator

try:
    import anthropic
except ImportError:
    raise ImportError("anthropic package required: pip install anthropic")

from llm.base import LLMProvider, JUDGE_SYSTEM, REFINE_SYSTEM


class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-opus-4-7"):
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def judge_input(self, value: str) -> dict:
        msg = await self._client.messages.create(
            model=self._model,
            max_tokens=512,
            system=JUDGE_SYSTEM,
            messages=[{"role": "user", "content": f"Input: {value}"}],
        )
        return json.loads(msg.content[0].text)

    async def stream_judge(self, value: str) -> AsyncIterator[str]:
        async with self._client.messages.stream(
            model=self._model,
            max_tokens=512,
            system=JUDGE_SYSTEM,
            messages=[{"role": "user", "content": f"Input: {value}"}],
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def refine_content(self, raw: str, source_url: str) -> dict:
        msg = await self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            system=REFINE_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": f"Source: {source_url}\n\nContent:\n{raw[:8000]}",
                }
            ],
        )
        return json.loads(msg.content[0].text)
