FROM python:3.12-slim

WORKDIR /app

COPY apps/agent-hub/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/agent-hub .
COPY packages /app/packages

ENV PYTHONPATH=/app/packages

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
