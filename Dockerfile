# Stage 1: build the React app
FROM node:22-slim AS ui
WORKDIR /ui
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python app that serves the API and the built UI
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OPSPILOT_MODE=auto OPSPILOT_EMBEDDINGS=tfidf
COPY requirements-lock.txt ./
RUN pip install --no-cache-dir -r requirements-lock.txt
COPY api/ api/
COPY opspilot/ opspilot/
COPY eval/ eval/
COPY data/ data/
COPY --from=ui /ui/dist frontend/dist
RUN mkdir -p docs && useradd -m app && chown -R app /app
USER app
EXPOSE 8000
# Fill the dashboard eval card on every start in offline mode (no API calls), then serve. Render sets $PORT.
CMD ["sh", "-c", "OPSPILOT_MODE=fallback python -m eval.run_eval > /dev/null; exec uvicorn api.serve:app --host 0.0.0.0 --port ${PORT:-8000}"]
