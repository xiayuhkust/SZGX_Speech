from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Speech Processing API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    DEEPSEEK_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()
