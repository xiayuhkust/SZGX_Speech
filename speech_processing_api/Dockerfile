FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt uvicorn

# Copy application code
COPY . .

# Make start script executable
COPY start.sh .
RUN chmod +x start.sh

# Expose the port
EXPOSE 8000

# Run using start script
CMD ["./start.sh"]
