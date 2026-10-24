"""
main.py — FastAPI Application Entrypoint

Configures:
- FastAPI app instance
- CORS Middleware for React frontend (Vite dev server)
- Debate API router registration
- Startup model verification logging
- Root health check endpoint
"""
import sys
import os
import logging


sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes_debate import router as debate_router
from config import ALLOWED_ORIGINS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agentic_debate_arena")

app = FastAPI(
    title="Agentic Debate Arena API",
    description="Logic-Verified Argument Coaching powered by Propositional Resolution & MCTS",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS + ["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(debate_router)


@app.on_event("startup")
def startup_event():
    """Startup verification logging model configurations."""
    logger.info("==================================================")
    logger.info(" ⚔️ Starting Agentic Debate Arena Backend")
    logger.info(" 🤖 Dynamic Model Orchestration: Groq LPU / NVIDIA NIM / Gemini")
    logger.info("==================================================")


@app.get("/")
def root():
    """Root health check endpoint."""
    return {
        "app": "Agentic Debate Arena API",
        "status": "online",
        "version": "1.0.0",
        "endpoints": [
            "POST /start-debate",
            "POST /next-turn",
            "GET /transcript/{debate_id}",
            "GET /mcts-trace/{debate_id}/{turn_number}",
            "GET /summary/{debate_id}",
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
