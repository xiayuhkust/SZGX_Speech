FROM python:3.12-slim

WORKDIR /app

# Install minimal dependencies
RUN pip install --no-cache-dir "fastapi[all]" "uvicorn[standard]"

# Copy application code
COPY app ./app

# Set environment variables
ENV PORT=8000
ENV HOST=0.0.0.0

# Start the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
