from abc import ABC, abstractmethod
from typing import AsyncIterator

JUDGE_SYSTEM = """You are a web crawling feasibility judge.
Given a keyword or URL, decide:
1. Whether it can be crawled (legal, accessible, non-harmful)
2. The best crawling method: rss | html | search
3. Recommended target sites (if keyword input)

Respond ONLY in this JSON format:
{
  "approved": true/false,
  "reason": "brief explanation",
  "crawl_method": "rss|html|search|null",
  "target_sites": ["url1", "url2"] or []
}"""

REFINE_SYSTEM = """You are a content curator for a personal knowledge blog.
Given raw crawled HTML/text content, produce a clean blog post in Korean.

Respond ONLY in this JSON format:
{
  "title": "concise title",
  "content": "full markdown content",
  "summary": "2-3 sentence summary",
  "tags": ["tag1", "tag2", "tag3"]
}"""


class LLMProvider(ABC):
    @abstractmethod
    async def judge_input(self, value: str) -> dict: ...

    @abstractmethod
    async def stream_judge(self, value: str) -> AsyncIterator[str]: ...

    @abstractmethod
    async def refine_content(self, raw: str, source_url: str) -> dict: ...
