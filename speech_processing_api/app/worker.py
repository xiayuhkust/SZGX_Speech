from celery import Celery
from app.services.text_processor import TextProcessor
from app.core.config import settings
import os

# Set environment variables for API keys
os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
os.environ["DEEPSEEK_API_KEY"] = settings.DEEPSEEK_API_KEY

celery_app = Celery(
    'text_processing',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

@celery_app.task(name='process_text')
def process_text(text_content: str):
    import asyncio
    processor = TextProcessor()
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(processor.process_text(text_content))
    return result
