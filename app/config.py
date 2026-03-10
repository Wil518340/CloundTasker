from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field

class Settings(BaseSettings):
    # Make project ID optional – if not set, Firestore client will try to auto-detect
    gcp_project_id: str | None = Field(default=None, validation_alias='GCP_PROJECT_ID')
    environment: str = Field(default="development", validation_alias='ENVIRONMENT')

    model_config = ConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()