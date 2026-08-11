"""
config.py — API keys (loaded from .env), model names, constants.
NEVER hardcode API keys here — always load from environment.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")
load_dotenv()

                  
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

                       
NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

                                 
GEMINI_MODEL: str = "gemini-3.6-flash"                                                         
GEMINI_MODEL_NAME: str = "gemini-3.6-flash"

NEMOTRON_CHAT_MODEL: str = "gemini-3.6-flash"                                                  
NEMOTRON_MODEL_NAME: str = "gemini-3.6-flash"

GEMINI_MODEL_FALLBACKS: list[str] = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
]

NVIDIA_MODEL_FALLBACKS: list[str] = [
    "nvidia/llama-3.3-nemotron-super-49b-v1",
    "meta/llama-3.1-8b-instruct",
    "meta/llama-3.1-70b-instruct",
]

GROQ_MODEL_FALLBACKS: list[str] = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
]

NEMOTRON_EMBED_MODEL: str = "nvidia/nemo-embed-qa-e5-v5"                                                

                        
MCTS_N_SIMULATIONS: int = 10

                             
FACT_BASE_SIZE: int = 20                                                 

              
ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]                           
