from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import agents, listings, open_houses, dashboard
from app.database.connection import engine, create_tables
from contextlib import asynccontextmanager
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables on startup
    create_tables()
    yield

app = FastAPI(
    title="Open House Matchmaker API",
    description="AI-powered real estate agent matching system for open houses",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS with environment-based origins
origins = [
    "http://localhost:3000",
    "http://localhost:8080",
]

if os.getenv("ENV") == "production":
    origins.append("https://your-production-site.com")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve React frontend if available
if os.path.isdir("frontend_build"):
    app.mount("/", StaticFiles(directory="frontend_build", html=True), name="frontend")

# Include API routers
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(listings.router, prefix="/api/v1/listings", tags=["listings"])
app.include_router(open_houses.router, prefix="/api/v1/open-houses", tags=["open-houses"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])

@app.get("/")
async def root():
    return {"message": "Open House Matchmaker API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    try:
        port = int(os.getenv("PORT", "8000"))
    except ValueError:
        port = 8000
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port)
