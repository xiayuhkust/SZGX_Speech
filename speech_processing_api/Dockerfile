FROM python:3.12-slim

WORKDIR /app

# Install minimal dependencies
RUN pip install --no-cache-dir fastapi==0.109.0 uvicorn[standard]==0.27.0

# Copy only main.py
COPY app/main.py ./app/main.py

# Set environment variables
ENV PORT=8000
ENV PYTHONPATH=/app

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
