# Prahari — Digital Public Safety Intelligence platform
FROM python:3.11-slim

# libgomp1: required by onnxruntime (Citizen Shield OCR)
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ backend/
COPY frontend/ frontend/
COPY sample_data/ sample_data/

ENV PORT=8008
EXPOSE 8008
CMD ["sh", "-c", "uvicorn app:app --app-dir backend --host 0.0.0.0 --port ${PORT}"]
