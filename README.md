# Earnings Call RAG Assistant

A comprehensive Streamlit application that extracts, stores, and queries earnings calls from Quantum and AI companies using RAG (Retrieval-Augmented Generation) with ChromaDB.

## Features

- 🔄 Automated extraction of earnings calls (2023-2025)
- 📊 Interactive UI with company, year, and quarter filters
- 🧠 RAG-powered Q&A system using ChromaDB
- 📈 Analytics and insights dashboard
- ⏰ Scheduled data updates
- 🔍 Advanced search and filtering

## Project Structure

```
earnings_rag_app/
├── app.py                 # Main Streamlit application
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── data/                 # Data storage directory
│   ├── raw/              # Raw earnings call data
│   ├── processed/        # Processed data
│   └── chroma_db/        # ChromaDB storage
├── src/
│   ├── __init__.py
│   ├── data_extractor.py # Earnings call extraction
│   ├── rag_system.py     # RAG implementation
│   ├── utils.py          # Utility functions
│   └── scheduler.py      # Automated extraction
├── logs/                 # Application logs
├── tests/                # Unit tests
└── README.md
```

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-username/earnings-rag-app.git
cd earnings-rag-app

# Run the setup script
python setup.py
```

### Option 2: Manual Setup

1. **Clone and setup environment:**
```bash
git clone https://github.com/your-username/earnings-rag-app.git
cd earnings-rag-app

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Install Ollama and models:**
```bash
# Install Ollama (visit https://ollama.ai for platform-specific instructions)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull required models
ollama pull llama3
ollama pull nomic-embed-text  # Optional but recommended
```

3. **Configure environment:**
```bash
# Create .env file
echo "ALPHA_VANTAGE_KEY=your_alpha_vantage_key" > .env
echo "OLLAMA_HOST=http://localhost:11434" > .env
```

4. **Create directories:**
```bash
mkdir -p data/raw data/processed data/chroma_db logs
```

5. **Start the application:**
```bash
streamlit run app.py
```

### Option 3: Docker Setup

```bash
# Clone repository
git clone https://github.com/your-username/earnings-rag-app.git
cd earnings-rag-app

# Create .env file
echo "ALPHA_VANTAGE_KEY=your_alpha_vantage_key" > .env

# Build and run with Docker Compose
docker-compose up --build

# Or run with Docker only
docker build -t earnings-rag-app .
docker run -p 8501:8501 -p 11434:11434 -v $(pwd)/data:/app/data earnings-rag-app
```

## First Time Usage

1. **Access the application** at `http://localhost:8501`

2. **Check system status** in the sidebar - ensure Ollama is connected

3. **Extract sample data:**
   - Select companies (start with NVDA, IBM)
   - Choose years (2024)
   - Select quarters (Q1, Q2, Q3)
   - Click "🔄 Extract Latest Data"

4. **Ask questions** in the Q&A tab:
   - "What were NVIDIA's key developments in AI?"
   - "How is IBM's quantum computing business performing?"
   - "Compare revenue growth across companies"

## Usage

1. Start the Streamlit application:
```bash
streamlit run app.py
```

2. Access the application at `http://localhost:8501`

3. Use the sidebar to:
   - Extract new earnings data
   - Filter by company, year, quarter
   - Ask questions about earnings calls

## Supported Companies

### AI Companies
- NVIDIA (NVDA)
- Microsoft (MSFT)
- Alphabet/Google (GOOGL)
- Meta (META)
- Tesla (TSLA)
- Amazon (AMZN)
- OpenAI (Private)
- Anthropic (Private)

### Quantum Computing Companies
- IBM (IBM)
- IonQ (IONQ)
- Rigetti Computing (RGTI)
- D-Wave Systems (QBTS)
- Quantum Computing Inc (QUBT)
- Arqit Quantum Inc (ARQQ)

## Features Overview

### Data Extraction
- Automated scraping from SEC filings
- Support for multiple data sources
- Real-time updates
- Error handling and retries

### RAG System
- ChromaDB vector storage
- Semantic search capabilities
- Context-aware responses
- Document chunking and embedding

### Analytics
- Company performance comparisons
- Trend analysis
- Interactive visualizations
- Export capabilities

## Prerequisites

- **Ollama**: Local LLM runtime (free)
- **Llama3**: Language model via Ollama (free)
- **Alpha Vantage API Key**: For financial data (free tier available)
- **SEC API**: No key required (rate limited)

## Troubleshooting

### Common Issues

**🔴 "Ollama is not running"**
- Ensure Ollama service is started: `ollama serve`
- Check if models are installed: `ollama list`
- Pull required models: `ollama pull llama3`

**🔴 "No relevant information found"**
- Extract data first using the sidebar controls
- Check that companies and time periods match your query
- Try rephrasing your question

**🔴 "Failed to extract earnings data"**
- Check your Alpha Vantage API key in .env file
- Verify internet connection
- Check logs in `logs/earnings_rag.log`

**🔴 "ChromaDB errors"**
- Delete `data/chroma_db` directory and restart
- Check disk space and permissions
- Ensure no other processes are using the database

### Performance Tips

- **First-time setup**: Allow 10-15 minutes for Ollama models to download
- **Query response time**: Typically 5-30 seconds depending on complexity
- **Data extraction**: Can take several minutes for multiple companies
- **Memory usage**: Ensure at least 4GB RAM available for Ollama

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI  │───▶│  Data Extractor  │───▶│   Raw Data      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                                               │
         ▼                                               ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Query Engine   │◀───│   RAG System     │◀───│  Text Chunking  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Llama3 (Ollama) │    │    ChromaDB      │    │   Embeddings    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Development

### Adding New Data Sources

1. **Extend EarningsExtractor** in `src/data_extractor.py`
2. **Add new extraction method** following the pattern of existing methods
3. **Update configuration** in `config.py` for new API endpoints
4. **Test extraction** using the built-in testing framework

### Customizing the RAG Pipeline

1. **Modify chunking strategy** in `RAGSystem._chunk_text()`
2. **Adjust embedding model** in `config.py` (`OLLAMA_EMBEDDING_MODEL`)
3. **Tune retrieval parameters** (`SIMILARITY_THRESHOLD`, `MAX_RETRIEVAL_RESULTS`)
4. **Customize prompt templates** in `RAGSystem.generate_answer()`

### Extending UI Features

1. **Add new tabs** in `app.py` main function
2. **Create custom visualizations** using Plotly
3. **Implement new filters** in the sidebar section
4. **Add export functionality** using pandas and streamlit

## Testing

```bash
# Run basic tests
python tests/test_basic.py

# Run with pytest
pip install pytest
pytest tests/ -v

# Run specific test categories
pytest tests/test_basic.py::TestUtils -v
```

## Deployment

### Production Deployment

**Using Docker Compose (Recommended):**
```bash
# Production docker-compose
version: '3.8'
services:
  earnings-rag:
    build: .
    ports:
      - "80:8501"
    environment:
      - STREAMLIT_SERVER_PORT=8501
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
    restart: always
    volumes:
      - /opt/earnings-data:/app/data
      - /opt/earnings-logs:/app/logs
```

**Environment Variables for Production:**
```bash
ALPHA_VANTAGE_KEY=your_production_key
OLLAMA_HOST=http://localhost:11434
LOG_LEVEL=WARNING
SCHEDULER_ENABLED=true
```

### Scaling Considerations

- **Multiple Instances**: Use a load balancer with sticky sessions
- **Database**: Consider PostgreSQL for metadata storage at scale
- **Caching**: Enable Redis profile in docker-compose for caching
- **Storage**: Use persistent volumes for data directory
- **Monitoring**: Implement health checks and monitoring

## Security Considerations

- **API Keys**: Store securely, rotate regularly
- **Network**: Use HTTPS in production, restrict API access
- **Data**: Implement data retention policies, backup regularly
- **Access**: Add authentication for production deployments

## Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes and test**: `python tests/test_basic.py`
4. **Commit changes**: `git commit -am 'Add amazing feature'`
5. **Push to branch**: `git push origin feature/amazing-feature`
6. **Create Pull Request**

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation for changes
- Test with multiple companies and time periods
- Ensure Docker builds successfully

### Reporting Issues

When reporting issues, please include:
- Operating system and Python version
- Complete error messages and logs
- Steps to reproduce the issue
- Expected vs actual behavior

## Roadmap

### Upcoming Features
- [ ] Real-time earnings call streaming
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] API endpoint for external access
- [ ] Sentiment analysis integration
- [ ] Comparative analysis tools

### Long-term Goals
- [ ] Support for international markets
- [ ] Integration with more data sources
- [ ] Advanced ML insights
- [ ] Mobile application
- [ ] Enterprise features

## License

MIT License - see [LICENSE](LICENSE) file for details

## Acknowledgments

- **Ollama**: For providing local LLM infrastructure
- **ChromaDB**: For vector database capabilities  
- **Streamlit**: For the amazing web framework
- **LangChain**: For RAG implementation patterns
- **Alpha Vantage**: For financial data API

## Support

- 📧 **Email**: [your-email@example.com]
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-username/earnings-rag-app/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-username/earnings-rag-app/discussions)
- 📖 **Documentation**: [Wiki](https://github.com/your-username/earnings-rag-app/wiki)

---

**Built with ❤️ for the financial analysis community**

*This project demonstrates the power of local LLMs and RAG systems for financial data analysis. Star ⭐ the repo if you find it useful!*
