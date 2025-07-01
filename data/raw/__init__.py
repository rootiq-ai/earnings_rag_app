"""
Earnings Call RAG Application - Source Package

This package contains the core modules for the earnings call RAG application:
- data_extractor: Handles earnings data extraction from various sources
- rag_system: Implements RAG using ChromaDB and Ollama Llama3
- utils: Utility functions and helpers
- scheduler: Automated data extraction and maintenance
"""

__version__ = "1.0.0"
__author__ = "Earnings RAG Team"
__description__ = "Earnings Call RAG Assistant with Ollama Llama3"

# Import main classes for easier access
from .data_extractor import EarningsExtractor
from .rag_system import RAGSystem
from .scheduler import DataScheduler

__all__ = [
    'EarningsExtractor',
    'RAGSystem', 
    'DataScheduler'
]
