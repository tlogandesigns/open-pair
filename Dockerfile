# Dockerfile

# 1. Build frontend
FROM node:18 AS ui
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# 2. Install backend
FROM python:3.11-slim AS api
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./

# 3. Final image
FROM python:3.11-slim
WORKDIR /app
COPY --from=ui /app/frontend/build ./frontend_build
COPY --from=api /app/backend ./

ENV PORT 8000
EXPOSE $PORT

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
