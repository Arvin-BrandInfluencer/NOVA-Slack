# ================================================
# FILE: common/config.py
# PURPOSE: Centralized configuration and client initialization
# ================================================
import os
import sys
from dotenv import load_dotenv
from loguru import logger
import google.generativeai as genai

# --- Loguru Configuration ---
logger.remove()
logger.add(sys.stderr, format="<yellow>{time:YYYY-MM-DD HH:mm:ss}</yellow> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>", colorize=True)

# --- Environment & Client Initialization ---
load_dotenv()
try:
    GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')
    logger.success("Shared Gemini client initialized successfully.")
except KeyError as e:
    logger.critical(f"FATAL: Missing GOOGLE_API_KEY. Please check .env file.")
    sys.exit(1)

# --- API Constants ---
BASE_API_URL = os.getenv("BASE_API_URL", "http://127.0.0.1:10000")
UNIFIED_API_URL = f"{BASE_API_URL}/api/influencer/query"

# --- Business Logic Constants ---
MARKET_CURRENCY_CONFIG = {
    'SWEDEN': {'rate': 11.30, 'symbol': 'SEK', 'name': 'SEK'},
    'NORWAY': {'rate': 11.50, 'symbol': 'NOK', 'name': 'NOK'},
    'DENMARK': {'rate': 7.46, 'symbol': 'DKK', 'name': 'DKK'},
    'UK': {'rate': 0.85, 'symbol': '£', 'name': 'GBP'},
    'FRANCE': {'rate': 1.0, 'symbol': '€', 'name': 'EUR'},
}
