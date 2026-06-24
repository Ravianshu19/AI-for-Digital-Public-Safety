# Prahari — container image for any host (Render, Hugging Face Spaces, Railway, Fly).
FROM python:3.11-slim

# System libs needed by OpenCV / onnxruntime (used by the OCR feature).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY sample_data/ ./sample_data/

# Hosts inject $PORT; default to 7860 (Hugging Face Spaces default).
ENV PORT=7860
EXPOSE 7860

CMD ["sh", "-c", "uvicorn app:app --app-dir backend --host 0.0.0.0 --port ${PORT:-7860}"]
