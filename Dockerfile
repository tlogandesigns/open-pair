# Build frontend
FROM node:18-slim as ui-build
WORKDIR /workspace
COPY frontend/package*.json frontend/
WORKDIR /workspace/frontend
RUN npm install
COPY frontend/ .
RUN npm run build

# Build backend
FROM python:3.11-slim as api-build
WORKDIR /workspace
COPY backend/requirements.txt backend/
RUN pip install -r backend/requirements.txt
COPY backend/ backend/

# Final image
FROM python:3.11-slim
WORKDIR /workspace

# Copy Python dependencies from build stage
COPY --from=api-build /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=api-build /usr/local/bin/ /usr/local/bin/

# Copy application files
COPY --from=api-build /workspace/backend ./
COPY --from=ui-build /workspace/frontend/build ./frontend_build

ENV PORT=8000
CMD uvicorn main:app --host=0.0.0.0 --port=$PORT