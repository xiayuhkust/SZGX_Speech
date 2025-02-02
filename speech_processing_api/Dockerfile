FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi==0.109.0 \
    "uvicorn[standard]"==0.27.0 \
    python-multipart==0.0.6 \
    openai==1.8.0 \
    python-dotenv==1.0.0 \
    pydantic==2.5.3 \
    pydantic-settings==2.1.0

COPY ./app ./app
COPY ./.env .

ENV PYTHONPATH=/app
ENV PORT=8000
ENV HOST=0.0.0.0

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
