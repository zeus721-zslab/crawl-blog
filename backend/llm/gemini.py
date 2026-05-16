import json
from typing import AsyncIterator

try:
    import google.generativeai as genai
except ImportError:
    genai = None  # type: ignore

from llm.base import LLMProvider, JUDGE_SYSTEM, REFINE_SYSTEM


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        if genai is None:
            raise ImportError(
                "google-generativeai required: pip install google-generativeai"
            )
        genai.configure(api_key=api_key)
        self._judge_model = genai.GenerativeModel(model, system_instruction=JUDGE_SYSTEM)
        self._refine_model = genai.GenerativeModel(model, system_instruction=REFINE_SYSTEM)

    async def judge_input(self, value: str) -> dict:
        resp = await self._judge_model.generate_content_async(f"Input: {value}")
        return json.loads(resp.text)

    async def stream_judge(self, value: str) -> AsyncIterator[str]:
        resp = await self._judge_model.generate_content_async(
            f"Input: {value}", stream=True
        )
        async for chunk in resp:
            if chunk.text:
                yield chunk.text

    async def refine_content(self, raw: str, source_url: str) -> dict:
        resp = await self._refine_model.generate_content_async(
            f"Source: {source_url}\n\nContent:\n{raw[:8000]}"
        )
        return json.loads(resp.text)
