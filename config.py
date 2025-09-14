# config.py
import os
from dotenv import load_dotenv
from google import genai 

load_dotenv() 
ES_HOST = os.getenv("ES_HOST")
INDEX_NAME = os.getenv("ES_INDEX")
CROSS_ENCODER_MODEL = os.getenv("CROSS_ENCODER_MODEL")
SEMANTIC_MODEL = os.getenv("SEMANTIC_MODEL")
# --- Gemini client ---
def get_gemini_client():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not found in environment")
    return genai.Client(api_key=api_key)