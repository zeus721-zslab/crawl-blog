from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # auth
    password_hash: str

    # LLM provider
    llm_provider: str = "claude"
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"

    # database
    db_host: str = "zslab_mariadb"
    db_port: int = 3306
    db_user: str = "crawl_blog"
    db_password: str = ""
    db_name: str = "crawl_blog"

    # limits
    claude_daily_limit: int = 100

    # app
    allowed_origins: str = "http://localhost:3000"
    domain_blacklist: str = ""

    @property
    def blacklisted_domains(self) -> set[str]:
        return {d.strip().lower() for d in self.domain_blacklist.split(",") if d.strip()}

    class Config:
        env_file = ".env"


settings = Settings()
