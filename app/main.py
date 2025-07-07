"""
BankBot FastAPI Application
Main application entry point with health check endpoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from .database import engine, Base
from .config import settings
from .routers import auth as auth_router
from .routers import rag as rag_router
from .routers import history as history_router

# Create FastAPI app instance
app = FastAPI(
    title="BankBot API",
    description="Intelligent Banking Assistant with Document Processing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

# Startup event
@app.on_event("startup")
async def startup():
    """Initialize database tables on startup"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Shutdown event
@app.on_event("shutdown")
async def shutdown():
    """Clean up resources on shutdown"""
    await engine.dispose()

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to BankBot API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Include routers
app.include_router(auth_router.router)
app.include_router(rag_router.router)
app.include_router(history_router.router)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    ) 