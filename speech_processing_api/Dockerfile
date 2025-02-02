FROM python:3.12-slim

WORKDIR /app

# Install dependencies without using virtualenv
RUN pip install --no-cache-dir \
    fastapi==0.109.0 \
    "uvicorn[standard]"==0.27.0 \
    python-multipart==0.0.6 \
    openai==1.8.0 \
    python-dotenv==1.0.0 \
    pydantic==2.5.3 \
    pydantic-settings==2.1.0

# Copy application files
COPY ./app ./app
COPY ./.env .
COPY start.sh .

# Make start script executable
RUN chmod +x start.sh

ENV PYTHONPATH=/app
ENV PORT=8000
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

# Use the start script directly
ENTRYPOINT ["/app/start.sh"]
