from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GROQ_API_KEY: str
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/crm_hcp"

    class Config:
        env_file = ".env"

settings = Settings()
