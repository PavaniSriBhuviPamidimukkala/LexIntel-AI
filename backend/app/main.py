from fastapi import FastAPI
from app.routes import health


app = FastAPI(
    title="LexIntel AI API",
    description="AI-powered Legal Intelligence Platform",
    version="1.0.0"
)


app.include_router(health.router)


@app.get("/")
def root():
    return {
        "project": "LexIntel AI",
        "message": "Backend API is running successfully 🚀"
    }