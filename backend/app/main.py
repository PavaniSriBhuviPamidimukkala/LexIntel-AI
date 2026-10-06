from fastapi import FastAPI
from app.routes import health, documents


app = FastAPI(
    title="LexIntel AI API",
    description="AI-powered Legal Intelligence Platform",
    version="1.0.0"
)


app.include_router(health.router)
app.include_router(documents.router)


@app.get("/")
def root():
    return {
        "project": "LexIntel AI",
        "message": "Backend API is running successfully 🚀"
    }
