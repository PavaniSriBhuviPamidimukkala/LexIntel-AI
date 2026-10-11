from fastapi import FastAPI
from app.routes import health, documents
from app.routes import ask
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.security import TrustedProxyAuthMiddleware

app = FastAPI(
    title="LexIntel AI API",
    description="AI-powered Legal Intelligence Platform",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
app.add_middleware(TrustedProxyAuthMiddleware)


app.include_router(health.router)
app.include_router(documents.router)
app.include_router(
    ask.router
)

@app.get("/")
def root():
    return {
        "project": "LexIntel AI",
        "message": "Backend API is running successfully 🚀"
    }
