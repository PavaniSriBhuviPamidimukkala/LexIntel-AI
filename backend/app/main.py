from fastapi import FastAPI
from app.routes import health, documents
from app.routes import ask
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="LexIntel AI API",
    description="AI-powered Legal Intelligence Platform",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://cuddly-space-pancake-69pw9v4r74wpc9j9-5173.app.github.dev/",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
