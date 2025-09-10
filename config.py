# config.py
import os
from dotenv import load_dotenv
import psycopg2
from google import genai 

load_dotenv()  # load .env ở cùng thư mục với main.py

def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
# --- Gemini client ---
def get_gemini_client():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not found in environment")
    return genai.Client(api_key=api_key)