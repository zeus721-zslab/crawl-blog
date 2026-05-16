# Deprecated: use llm.factory.get_llm() instead.
# This shim exists for backward compatibility only.
from llm.factory import get_llm as _get


async def judge_input(value: str) -> dict:
    return await _get().judge_input(value)


async def stream_judge(value: str):
    async for chunk in _get().stream_judge(value):
        yield chunk


async def refine_content(raw: str, source_url: str) -> dict:
    return await _get().refine_content(raw, source_url)
