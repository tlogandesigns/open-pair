from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import agents, listings, open_houses, dashboard
from app.database.connection import engine, create_tables
from contextlib import asynccontextmanager

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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    uvicorn.run(app, host="0.0.0.0", port=8000)
