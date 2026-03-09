from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    gcp_project_id: str
    environment: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()