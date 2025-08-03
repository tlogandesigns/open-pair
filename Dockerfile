# Build frontend
FROM node:18-slim AS ui-build
WORKDIR /app
COPY frontend/package*.json frontend/
WORKDIR /app/frontend
RUN npm install --only=production
COPY frontend/ .
RUN npm run build

# Build backend
FROM python:3.11-slim AS api-build
WORKDIR /app
COPY backend/requirements.txt backend/
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ backend/

# Final image
FROM python:3.11-slim
WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from build stage
COPY --from=api-build /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=api-build /usr/local/bin/ /usr/local/bin/

# Copy application files
COPY --from=api-build /app/backend ./app
COPY --from=ui-build /app/frontend/build ./frontend_build

# Copy startup script
COPY start.sh ./
RUN chmod +x start.sh

# Set the Python path to include the current directory
ENV PYTHONPATH="/app"
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

CMD ["./start.sh"]
