"""
Configuration settings for the Earnings Call RAG Application
"""

import os
from dotenv import load_dotenv
from typing import Dict, List

# Load environment variables
load_dotenv()

# Ollama Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = "llama3"
OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"

# API Keys
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")

# Application Settings
APP_TITLE = "Earnings Call RAG Assistant"
APP_ICON = "📊"
DATA_UPDATE_INTERVAL = 3600  # 1 hour in seconds

# Directory Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
CHROMA_DB_DIR = os.path.join(DATA_DIR, "chroma_db")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Ensure directories exist
for directory in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, CHROMA_DB_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Time Periods
YEARS = ["2023", "2024", "2025"]
QUARTERS = ["Q1", "Q2", "Q3", "Q4"]

# Company Information
AI_COMPANIES = {
    "NVDA": {"name": "NVIDIA Corporation", "sector": "AI Hardware"},
    "MSFT": {"name": "Microsoft Corporation", "sector": "AI Software"},
    "GOOGL": {"name": "Alphabet Inc.", "sector": "AI Software"},
    "META": {"name": "Meta Platforms Inc.", "sector": "AI Software"},
    "TSLA": {"name": "Tesla Inc.", "sector": "AI/Automotive"},
    "AMZN": {"name": "Amazon.com Inc.", "sector": "AI/Cloud"},
    "CRM": {"name": "Salesforce Inc.", "sector": "AI Software"},
    "ORCL": {"name": "Oracle Corporation", "sector": "AI/Database"},
    "AMD": {"name": "Advanced Micro Devices", "sector": "AI Hardware"},
    "INTC": {"name": "Intel Corporation", "sector": "AI Hardware"}
}

QUANTUM_COMPANIES = {
    "IBM": {"name": "International Business Machines", "sector": "Quantum Computing"},
    "IONQ": {"name": "IonQ Inc.", "sector": "Quantum Computing"},
    "RGTI": {"name": "Rigetti Computing Inc.", "sector": "Quantum Computing"},
    "QBTS": {"name": "D-Wave Quantum Inc.", "sector": "Quantum Computing"},
    "QUBT": {"name": "Quantum Computing Inc.", "sector": "Quantum Computing"},
    "ARQQ": {"name": "Arqit Quantum Inc.", "sector": "Quantum Security"},
    "QTUM": {"name": "Defiance Quantum ETF", "sector": "Quantum ETF"},
    "ATOM": {"name": "Atomera Incorporated", "sector": "Quantum Materials"}
}

# Combine all companies
COMPANIES = {**AI_COMPANIES, **QUANTUM_COMPANIES}

# Data Sources Configuration
SEC_BASE_URL = "https://www.sec.gov"
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

# ChromaDB Configuration
CHROMA_COLLECTION_NAME = "earnings_calls"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# RAG Configuration
MAX_CONTEXT_LENGTH = 4000
SIMILARITY_THRESHOLD = 0.7
MAX_RETRIEVAL_RESULTS = 5

# Extraction Configuration
EXTRACTION_BATCH_SIZE = 5
MAX_RETRIES = 3
REQUEST_DELAY = 1  # seconds between requests

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = os.path.join(LOGS_DIR, "earnings_rag.log")

# UI Configuration
SIDEBAR_WIDTH = 300
MAIN_CONTENT_WIDTH = 1200

# Scheduler Configuration
SCHEDULER_ENABLED = True
DAILY_UPDATE_TIME = "09:00"  # 9 AM
WEEKLY_FULL_SYNC = "sunday"

# Error Messages
ERROR_MESSAGES = {
    "ollama_connection": "Unable to connect to Ollama. Please ensure Ollama is running.",
    "model_not_found": "Required model not found. Please run 'ollama pull llama3'",
    "api_key_missing": "API key is missing. Please check your .env file.",
    "data_extraction_failed": "Failed to extract earnings data. Please try again.",
    "chroma_db_error": "Database error occurred. Please check the logs."
}

# Success Messages
SUCCESS_MESSAGES = {
    "data_extracted": "Successfully extracted earnings data!",
    "data_stored": "Data successfully stored in vector database!",
    "query_completed": "Query completed successfully!"
}
