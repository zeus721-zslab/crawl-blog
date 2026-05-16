import json
import logging
import re

try:
    import anthropic
except ImportError:
    raise ImportError("anthropic package required: pip install anthropic")

from llm.base import LLMProvider, JUDGE_SYSTEM, REFINE_SYSTEM

log = logging.getLogger(__name__)

JUDGE_MODEL = "claude-haiku-4-5"
REFINE_MODEL = "claude-sonnet-4-5"


def _parse_json(text: str, context: str) -> dict:
    """Strip markdown code fences if present, then parse JSON. Log raw on failure."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ``` wrappers
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        log.error("%s JSON parse failed | error=%s | raw=%r", context, e, text)
        raise


class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str):
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    async def judge_input(self, value: str) -> dict:
        is_url = value.startswith("http://") or value.startswith("https://")
        label = "URL" if is_url else "keyword/topic"
        msg = await self._client.messages.create(
            model=JUDGE_MODEL,
            max_tokens=768,
            system=JUDGE_SYSTEM,
            messages=[{"role": "user", "content": f"{label}: {value}"}],
        )
        return _parse_json(msg.content[0].text, "judge_input")

    async def refine_content(self, raw: str, source_url: str) -> dict:
        msg = await self._client.messages.create(
            model=REFINE_MODEL,
            max_tokens=2048,
            system=REFINE_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": f"Source: {source_url}\n\nContent:\n{raw[:8000]}",
                }
            ],
        )
        return _parse_json(msg.content[0].text, "refine_content")
