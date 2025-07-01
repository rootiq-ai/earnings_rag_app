"""
Basic tests for the Earnings Call RAG Application
"""

import pytest
import os
import sys

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_extractor import EarningsExtractor
from rag_system import RAGSystem
from utils import format_currency, format_percentage, validate_company_ticker
import config

class TestDataExtractor:
    """Test the data extractor functionality"""
    
    def test_extractor_initialization(self):
        """Test that extractor initializes properly"""
        extractor = EarningsExtractor()
        assert extractor is not None
        assert hasattr(extractor, 'session')
    
    def test_sample_data_generation(self):
        """Test sample data generation"""
        extractor = EarningsExtractor()
        result = extractor._generate_sample_data('NVDA', '2024', 'Q1')
        
        assert result is not None
        assert 'content' in result
        assert 'source' in result
        assert result['company'] == 'NVDA'
        assert result['year'] == '2024'
        assert result['quarter'] == 'Q1'
    
    def test_batch_extraction(self):
        """Test batch extraction with sample data"""
        extractor = EarningsExtractor()
        results = extractor.batch_extract(['NVDA'], ['2024'], ['Q1'])
        
        assert 'successful' in results
        assert 'failed' in results
        assert 'details' in results

class TestRAGSystem:
    """Test the RAG system functionality"""
    
    def test_rag_initialization(self):
        """Test RAG system initialization"""
        try:
            rag_system = RAGSystem()
            assert rag_system is not None
        except Exception as e:
            # RAG system might fail if Ollama is not running, which is expected
            assert "ollama" in str(e).lower() or "chroma" in str(e).lower()
    
    def test_text_chunking(self):
        """Test text chunking functionality"""
        rag_system = RAGSystem()
        
        # Create a long text
        long_text = " ".join(["This is a test sentence."] * 200)
        chunks = rag_system._chunk_text(long_text)
        
        assert len(chunks) > 1
        assert all(len(chunk.split()) <= config.CHUNK_SIZE for chunk in chunks)

class TestUtils:
    """Test utility functions"""
    
    def test_format_currency(self):
        """Test currency formatting"""
        assert format_currency(1000000) == "$1.0M USD"
        assert format_currency(1500000000) == "$1.5B USD"
        assert format_currency(500) == "$500.00 USD"
    
    def test_format_percentage(self):
        """Test percentage formatting"""
        assert format_percentage(15.678) == "15.7%"
        assert format_percentage(100.0, 0) == "100%"
    
    def test_validate_company_ticker(self):
        """Test company ticker validation"""
        assert validate_company_ticker('NVDA') == True
        assert validate_company_ticker('nvda') == True
        assert validate_company_ticker('INVALID') == False

class TestConfig:
    """Test configuration settings"""
    
    def test_config_constants(self):
        """Test that config constants are properly set"""
        assert hasattr(config, 'COMPANIES')
        assert hasattr(config, 'YEARS')
        assert hasattr(config, 'QUARTERS')
        assert hasattr(config, 'OLLAMA_MODEL')
        
        assert config.OLLAMA_MODEL == 'llama3'
        assert len(config.COMPANIES) > 0
        assert len(config.YEARS) > 0
    
    def test_company_data(self):
        """Test company data structure"""
        for ticker, info in config.COMPANIES.items():
            assert 'name' in info
            assert 'sector' in info
            assert isinstance(ticker, str)
            assert len(ticker) <= 6  # Stock tickers are typically 1-5 characters

if __name__ == "__main__":
    # Run basic tests
    print("Running basic tests...")
    
    # Test configuration
    print("✓ Config loaded")
    
    # Test data extractor
    try:
        extractor = EarningsExtractor()
        print("✓ Data extractor initialized")
    except Exception as e:
        print(f"✗ Data extractor failed: {e}")
    
    # Test RAG system (might fail if Ollama not running)
    try:
        rag_system = RAGSystem()
        print("✓ RAG system initialized")
    except Exception as e:
        print(f"! RAG system warning (expected if Ollama not running): {e}")
    
    # Test utilities
    try:
        from utils import format_currency, setup_logging
        assert format_currency(1000000) == "$1.0M USD"
        print("✓ Utilities working")
    except Exception as e:
        print(f"✗ Utilities failed: {e}")
    
    print("\nBasic tests completed!")
    print("To run with pytest: pytest tests/test_basic.py -v")
