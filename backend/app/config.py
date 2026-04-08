from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://hcp_user:hcp_pass@localhost:5432/hcp_db"
    GROQ_API_KEY: str = ""

    model_config = {"env_file": ".env"}



settings = Settings()


print("GROQ KEY:", settings.GROQ_API_KEY)