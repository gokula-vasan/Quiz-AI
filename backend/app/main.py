from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import connect_db, close_db
from app.auth.routes import router as auth_router
from app.routes.documents import router as doc_router
from app.routes.quizzes import router as quiz_router
from app.routes.progress import router as progress_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB
    await connect_db()
    yield
    # Shutdown: Close MongoDB connection
    await close_db()

app = FastAPI(
    title="QuizMaster AI - Multi-Agent Learning Assistant",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for local development (React on Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production environments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers under standard prefix /api
app.include_router(auth_router, prefix="/api")
app.include_router(doc_router, prefix="/api")
app.include_router(quiz_router, prefix="/api")
app.include_router(progress_router, prefix="/api")

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "QuizMaster AI Backend Server",
        "timestamp": "active"
    }
