from llm.base import LLMProvider


class MockProvider(LLMProvider):
    async def judge_input(self, value: str) -> dict:
        return {
            "approved": True,
            "reason": "mock",
            "crawl_method": "html",
            "name": value[:50],
            "target_sites": [],
        }

    async def refine_content(self, raw: str, source_url: str, feed_name: str | None = None, keyword: str | None = None) -> dict:
        title = (raw[:80].strip().splitlines()[0] if raw.strip() else source_url)
        return {
            "title": title,
            "content": raw[:4000],
            "summary": raw[:200],
            "tags": ["mock"],
        }
