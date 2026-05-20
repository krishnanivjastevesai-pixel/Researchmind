"""
Configuration Module
Centralized configuration management for the ResearchMind application.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================
# Directory Structure
# ============================================
BASE_DIR = Path(__file__).parent
CACHE_DIR = BASE_DIR / ".cache"
LOGS_DIR = BASE_DIR / "logs"
REPORTS_DIR = BASE_DIR / "reports"

# Create directories if they don't exist
CACHE_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# ============================================
# API Configuration
# ============================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# ============================================
# Model Configuration
# ============================================
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.0"))

# ============================================
# Application Settings
# ============================================
MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "5"))
MAX_SCRAPE_LENGTH = int(os.getenv("MAX_SCRAPE_LENGTH", "3000"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "8"))

# ============================================
# Cache Settings
# ============================================
ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"
CACHE_EXPIRY_HOURS = int(os.getenv("CACHE_EXPIRY_HOURS", "24"))

# ============================================
# Retry Settings
# ============================================
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_MIN_WAIT = int(os.getenv("RETRY_MIN_WAIT", "1"))
RETRY_MAX_WAIT = int(os.getenv("RETRY_MAX_WAIT", "10"))

# ============================================
# Validation Settings
# ============================================
MIN_TOPIC_LENGTH = int(os.getenv("MIN_TOPIC_LENGTH", "3"))
MAX_TOPIC_LENGTH = int(os.getenv("MAX_TOPIC_LENGTH", "200"))

# ============================================
# Logging Configuration
# ============================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "research.log"
