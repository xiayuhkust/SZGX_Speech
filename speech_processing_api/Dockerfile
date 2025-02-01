FROM python:3.12-slim

WORKDIR /app

# Install system dependencies and Python packages directly
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir fastapi==0.109.0 uvicorn[standard]==0.27.0 python-multipart==0.0.6 openai==1.8.0 python-dotenv==1.0.0 pydantic==2.5.3 pydantic-settings==2.1.0 typing_extensions==4.9.0

# Copy application code
COPY app ./app
COPY .env .

# Set environment variables
ENV PORT=8000
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
