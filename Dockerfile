### Build frontend
FROM node:18 AS ui-build
WORKDIR /workspace/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

### Build backend
FROM python:3.11-slim AS api-build
WORKDIR /workspace/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./

### Final image
FROM python:3.11-slim
WORKDIR /workspace
# Copy backend
COPY --from=api-build /workspace/backend ./
# Copy frontend output
COPY --from=ui-build /workspace/frontend/build ./frontend_build

ENV PORT=8000
CMD uvicorn main:app --host=0.0.0.0 --port=$PORT
