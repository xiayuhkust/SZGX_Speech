FROM python:3.12-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir fastapi==0.109.0 uvicorn==0.27.0 python-multipart==0.0.6 openai==1.8.0 python-dotenv==1.0.0 pydantic==2.5.3 pydantic-settings==2.1.0

# Copy only necessary files
COPY ./app ./app
COPY ./requirements.txt .
COPY ./.env .

# Start the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
