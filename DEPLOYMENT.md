# Deployment Guide

## Docker Deployment

### Building and Running with Docker

```bash
# Build the image
docker build -t open-house-matchmaker .

# Run the container
docker run -p 8000:8000 open-house-matchmaker
```

### Using Docker Compose

```bash
# Start the application
docker-compose up --build

# Run in detached mode
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

## Railway Deployment

The project is configured for Railway deployment with `railway.json`:

```bash
# Deploy to Railway
railway up
```

## Environment Variables

- `PORT`: Server port (default: 8000)
- `ENV`: Environment (development/production)

## Troubleshooting

### ModuleNotFoundError: No module named 'backend'

This error typically occurs when the module path is incorrect. The fix involves:

1. **Correct Working Directory**: Ensure the Dockerfile sets `WORKDIR /app`
2. **Proper File Copying**: Backend files should be copied to the root of the working directory
3. **Python Path**: Set `PYTHONPATH="/app"` to ensure module resolution
4. **Uvicorn Command**: Use `uvicorn main:app` (not `backend.main:app`) since files are in the root

### Container Structure

After building, the container should have this structure:
```
/app/
├── main.py              # FastAPI application entry point
├── app/                 # Application modules
│   ├── __init__.py
│   ├── api/             # API routes
│   ├── database/        # Database models and connection
│   ├── ml/              # Machine learning components
│   └── services/        # Business logic services
├── frontend_build/      # Built React frontend
└── start.sh            # Startup script
```

### Debug Container

To debug the container:

```bash
# Build and run with debugging
docker build -t open-house-matchmaker .
docker run -it --entrypoint /bin/bash open-house-matchmaker

# Inside the container, check structure
ls -la
python3 -c "from main import app; print('Success')"
```

### Health Check

The application includes a health check endpoint at `/health` that can be used to verify the service is running correctly.

## Production Considerations

1. **Database**: Configure PostgreSQL for production (uncomment in docker-compose.yml)
2. **Environment Variables**: Set proper environment variables for production
3. **SSL/HTTPS**: Configure reverse proxy (nginx, traefik) for SSL termination
4. **Monitoring**: Add logging and monitoring solutions
5. **Scaling**: Use container orchestration (Kubernetes, Docker Swarm) for scaling
