"""
Setup script for Earnings Call RAG Application
"""

import os
import sys
import subprocess
from pathlib import Path

def create_directories():
    """Create necessary directories"""
    directories = [
        'data',
        'data/raw',
        'data/processed', 
        'data/chroma_db',
        'data/backups',
        'logs',
        'src',
        'tests'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def create_env_file():
    """Create .env file template"""
    env_template = """# Earnings Call RAG Application Environment Variables

# Alpha Vantage API Key (get free key from https://www.alphavantage.co/support/#api-key)
ALPHA_VANTAGE_KEY=your_alpha_vantage_key_here

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434

# Optional: Set log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_template)
        print("✓ Created .env file template")
    else:
        print("! .env file already exists, skipping")

def check_ollama():
    """Check if Ollama is installed and running"""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Ollama is installed and running")
            
            # Check if llama3 is available
            if 'llama3' in result.stdout:
                print("✓ Llama3 model is available")
            else:
                print("! Llama3 model not found. Run: ollama pull llama3")
                return False
        else:
            print("! Ollama is not running. Please start Ollama service")
            return False
    except FileNotFoundError:
        print("! Ollama is not installed. Please install from https://ollama.ai")
        return False
    
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False

def run_basic_tests():
    """Run basic system tests"""
    print("Running basic tests...")
    try:
        # Import and test basic functionality
        sys.path.append('src')
        from data_extractor import EarningsExtractor
        from utils import format_currency
        
        # Test extractor
        extractor = EarningsExtractor()
        
        # Test utilities
        assert format_currency(1000000) == "$1.0M USD"
        
        print("✓ Basic tests passed")
        return True
    except Exception as e:
        print(f"! Some tests failed (this may be expected): {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Earnings Call RAG Application\n")
    
    # Create directories
    print("1. Creating directories...")
    create_directories()
    print()
    
    # Create .env file
    print("2. Setting up environment...")
    create_env_file()
    print()
    
    # Install dependencies
    print("3. Installing dependencies...")
    if install_dependencies():
        print()
    else:
        print("⚠️  Dependency installation failed. Please run manually:")
        print("pip install -r requirements.txt")
        print()
    
    # Check Ollama
    print("4. Checking Ollama setup...")
    ollama_ok = check_ollama()
    print()
    
    # Run tests
    print("5. Running basic tests...")
    tests_ok = run_basic_tests()
    print()
    
    # Final status
    print("🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Edit .env file with your API keys")
    
    if not ollama_ok:
        print("2. Install and start Ollama:")
        print("   - Visit https://ollama.ai for installation")
        print("   - Run: ollama pull llama3")
        print("   - Run: ollama pull nomic-embed-text")
    
    print("3. Start the application:")
    print("   streamlit run app.py")
    
    print("\nFor help, see README.md or visit the GitHub repository")

if __name__ == "__main__":
    main()
