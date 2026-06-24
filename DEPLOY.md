# Deploying Prahari (free hosting)

The repo is container-ready (`Dockerfile`) and has a Render blueprint (`render.yaml`).
The app binds to `0.0.0.0` and honours the host's `$PORT`.

## Option A — Render.com (simplest, connects to GitHub)
1. Push the repo to GitHub (already done).
2. Go to <https://render.com> → sign in with GitHub.
3. **New +  →  Blueprint**, pick this repo. Render reads `render.yaml` and builds
   the Docker image (so OpenCV/onnxruntime for OCR work).
4. Click **Apply**. First build takes a few minutes; you get a URL like
   `https://prahari.onrender.com`.
- Free tier sleeps after ~15 min idle → the first hit wakes it (~30–60 s), then it's fast.
- Health check: `/api/health`.

## Option B — Hugging Face Spaces (more RAM, best for the OCR feature)
1. <https://huggingface.co/new-space> → **SDK: Docker** → create the Space.
2. Push these files to the Space's git (it builds the `Dockerfile` automatically),
   or upload them via the web UI.
3. Free CPU basic gives 16 GB RAM — comfortable for the OCR (RapidOCR/ONNX) model.
   The app listens on `7860` (the Space default), already set in the `Dockerfile`.

## Option C — any container host (Railway, Fly.io, Cloud Run)
Build and run the image directly:
```bash
docker build -t prahari .
docker run -p 8008:7860 -e PORT=7860 prahari
# open http://localhost:8008
```

## Notes
- **Cold starts** on free tiers: hit the URL ~1 minute before a live demo to wake it.
- **OCR memory**: the screenshot-OCR feature loads an ONNX model (~hundreds of MB peak).
  It works comfortably on Hugging Face Spaces / paid tiers; on Render's 512 MB free
  instance it may be tight — every other feature runs fine, and OCR degrades gracefully.
- The audit ledger writes to `backend/audit_log.jsonl` (ephemeral on free hosts; fine for demos).
