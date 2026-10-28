from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extras="ignore")
    shopify_shop: str
    shopify_client_id: str
    shopify_client_secret: str
    shopify_api_version: str = 2026 - 10

    anthropic_api_key: str
    claude_model: str = "claude-sonnet-5-5"

    database_url: str
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384
    top_k: int = 5


settings = Settings()
