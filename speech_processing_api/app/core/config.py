from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    PROJECT_NAME: str = "Speech Processing API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

settings = Settings()
