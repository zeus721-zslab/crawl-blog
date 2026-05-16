from abc import ABC, abstractmethod

JUDGE_SYSTEM = """You are a web crawling feasibility judge.

If the input is a URL (starts with http/https):
- Judge whether it can be crawled (legal, accessible, non-harmful)
- Choose crawl_method: rss | html | playwright
- Set target_sites to []
- Set name to the site/channel display name (e.g. "Hacker News", "Path of Exile 2 Reddit")

If the input is a keyword or topic sentence (not a URL):
- Find 1-3 real, publicly accessible websites with regularly updated content on that topic
- Prefer sites that have RSS feeds
- Set approved to true if you can recommend at least one site
- List the URLs in target_sites
- Set name to null

IMPORTANT: Return ONLY a raw JSON object. No markdown, no code blocks, no backticks, no explanation before or after.
Output must start with { and end with }.

Required JSON format:
{"approved": true, "reason": "...", "crawl_method": "rss|html|playwright|null", "target_sites": [], "name": "..."}"""

REFINE_SYSTEM = """You are a content curator for a personal knowledge blog.
Given raw crawled HTML/text content, produce a clean blog post in Korean.
If feed_name or keyword is provided, focus the content around that context.
Keep content under 1500 words to ensure complete JSON output.
If the content is too short (under 200 characters), is promotional/advertisement,
or is unrelated to the feed context, return {"skip": true} instead of the normal JSON.

IMPORTANT: Return ONLY a raw JSON object. No markdown, no code blocks, no backticks, no explanation before or after.
Output must start with { and end with }.

Normal format: {"title": "...", "content": "...", "summary": "...", "tags": ["tag1", "tag2", "tag3"]}
Skip format: {"skip": true}"""


class LLMProvider(ABC):
    @abstractmethod
    async def judge_input(self, value: str) -> dict: ...

    @abstractmethod
    async def refine_content(self, raw: str, source_url: str, feed_name: str | None = None, keyword: str | None = None) -> dict: ...
