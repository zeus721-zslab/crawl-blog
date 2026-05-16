from abc import ABC, abstractmethod

JUDGE_SYSTEM = """You are a web crawling feasibility judge.

If the input is a URL (starts with http/https):
- Judge whether it can be crawled (legal, accessible, non-harmful)
- Choose crawl_method: rss | html | playwright
- Set target_sites to []

If the input is a keyword or topic sentence (not a URL):
- Find 1-3 real, publicly accessible websites with regularly updated content on that topic
- Prefer sites that have RSS feeds
- Set approved to true if you can recommend at least one site
- List the URLs in target_sites

IMPORTANT: Return ONLY a raw JSON object. No markdown, no code blocks, no backticks, no explanation before or after.
Output must start with { and end with }.

Required JSON format:
{"approved": true, "reason": "...", "crawl_method": "rss|html|playwright|null", "target_sites": []}"""

REFINE_SYSTEM = """You are a content curator for a personal knowledge blog.
Given raw crawled HTML/text content, produce a clean blog post in Korean.
Keep content under 1500 words to ensure complete JSON output.

IMPORTANT: Return ONLY a raw JSON object. No markdown, no code blocks, no backticks, no explanation before or after.
Output must start with { and end with }.

Required JSON format:
{"title": "...", "content": "...", "summary": "...", "tags": ["tag1", "tag2", "tag3"]}"""


class LLMProvider(ABC):
    @abstractmethod
    async def judge_input(self, value: str) -> dict: ...

    @abstractmethod
    async def refine_content(self, raw: str, source_url: str) -> dict: ...
