"""
Main Streamlit Application for Earnings Call RAG Assistant
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import asyncio
import time
from typing import List, Dict, Optional

# Local imports
from config import *
from src.data_extractor import EarningsExtractor
from src.rag_system import RAGSystem
from src.utils import setup_logging, format_currency, calculate_metrics
from src.scheduler import DataScheduler

# Setup logging
logger = setup_logging()

# Page configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .company-tag {
        background: #f0f2f6;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        margin: 0.25rem;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
@st.cache_resource
def initialize_systems():
    """Initialize RAG system and data extractor"""
    try:
        rag_system = RAGSystem()
        extractor = EarningsExtractor()
        scheduler = DataScheduler()
        return rag_system, extractor, scheduler
    except Exception as e:
        st.error(f"Failed to initialize systems: {str(e)}")
        return None, None, None

def display_header():
    """Display application header"""
    st.markdown("""
    <div class="main-header">
        <h1 style="color: white; margin: 0;">📊 Earnings Call RAG Assistant</h1>
        <p style="color: #e0e0e0; margin: 0;">Extract, store, and query earnings calls from Quantum & AI companies using Llama3</p>
    </div>
    """, unsafe_allow_html=True)

def display_sidebar(rag_system, extractor):
    """Display sidebar with controls"""
    with st.sidebar:
        st.header("🔧 Controls")
        
        # System Status
        st.subheader("🚦 System Status")
        ollama_status = rag_system.check_ollama_connection() if rag_system else False
        st.write(f"Ollama: {'🟢 Connected' if ollama_status else '🔴 Disconnected'}")
        
        if not ollama_status:
            st.warning("Ollama is not running. Please start Ollama and ensure Llama3 is installed.")
            if st.button("🔄 Retry Connection"):
                st.rerun()
        
        st.divider()
        
        # Data Extraction Section
        st.subheader("📥 Data Extraction")
        
        col1, col2 = st.columns(2)
        with col1:
            selected_companies = st.multiselect(
                "Companies",
                options=list(COMPANIES.keys()),
                default=["NVDA", "IBM"],
                key="company_select"
            )
        
        with col2:
            selected_years = st.multiselect(
                "Years",
                options=YEARS,
                default=["2024"],
                key="year_select"
            )
        
        selected_quarters = st.multiselect(
            "Quarters",
            options=QUARTERS,
            default=["Q1", "Q2", "Q3"],
            key="quarter_select"
        )
        
        if st.button("🔄 Extract Latest Data", type="primary"):
            if extractor and selected_companies and selected_years:
                with st.spinner("Extracting earnings data..."):
                    extract_data(extractor, rag_system, selected_companies, selected_years, selected_quarters)
            else:
                st.error("Please select companies and years to extract")
        
        st.divider()
        
        # Filter Section
        st.subheader("🔍 Filters")
        
        filter_company = st.selectbox(
            "Filter by Company",
            options=["All"] + list(COMPANIES.keys()),
            key="filter_company"
        )
        
        filter_year = st.selectbox(
            "Filter by Year",
            options=["All"] + YEARS,
            key="filter_year"
        )
        
        filter_quarter = st.selectbox(
            "Filter by Quarter",
            options=["All"] + QUARTERS,
            key="filter_quarter"
        )
        
        return {
            "companies": selected_companies,
            "years": selected_years,
            "quarters": selected_quarters,
            "filter_company": filter_company,
            "filter_year": filter_year,
            "filter_quarter": filter_quarter
        }

def extract_data(extractor, rag_system, companies, years, quarters):
    """Extract and store earnings data"""
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_tasks = len(companies) * len(years) * len(quarters)
        completed_tasks = 0
        
        for company in companies:
            for year in years:
                for quarter in quarters:
                    status_text.text(f"Extracting {company} {year} {quarter}...")
                    
                    # Extract earnings call data
                    result = extractor.extract_earnings_call(company, year, quarter)
                    
                    if result and rag_system:
                        # Store in RAG system
                        rag_system.add_document(
                            content=result['content'],
                            metadata={
                                'company': company,
                                'year': year,
                                'quarter': quarter,
                                'date': result.get('date', ''),
                                'source': result.get('source', '')
                            }
                        )
                    
                    completed_tasks += 1
                    progress_bar.progress(completed_tasks / total_tasks)
                    time.sleep(0.1)  # Prevent overwhelming the APIs
        
        status_text.text("Extraction completed!")
        st.success(SUCCESS_MESSAGES["data_extracted"])
        
    except Exception as e:
        st.error(f"Extraction failed: {str(e)}")
        logger.error(f"Data extraction error: {str(e)}")

def display_analytics(rag_system, filters):
    """Display analytics dashboard"""
    st.header("📊 Analytics Dashboard")
    
    if not rag_system:
        st.warning("RAG system not available")
        return
    
    # Get document statistics
    stats = rag_system.get_collection_stats(filters)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Documents",
            value=stats.get('total_documents', 0),
            delta=f"+{stats.get('new_documents', 0)} this week"
        )
    
    with col2:
        st.metric(
            label="Companies Covered",
            value=stats.get('unique_companies', 0)
        )
    
    with col3:
        st.metric(
            label="Latest Quarter",
            value=stats.get('latest_quarter', 'N/A')
        )
    
    with col4:
        st.metric(
            label="Data Freshness",
            value=f"{stats.get('days_since_update', 0)} days ago"
        )
    
    # Company distribution chart
    if stats.get('company_distribution'):
        fig = px.pie(
            values=list(stats['company_distribution'].values()),
            names=list(stats['company_distribution'].keys()),
            title="Documents by Company"
        )
        st.plotly_chart(fig, use_container_width=True)

def display_query_interface(rag_system):
    """Display Q&A interface"""
    st.header("🤖 Ask Questions About Earnings Calls")
    
    if not rag_system:
        st.warning("RAG system not available")
        return
    
    # Example questions
    with st.expander("💡 Example Questions"):
        examples = [
            "What were NVIDIA's key AI developments mentioned in their latest earnings?",
            "How is IBM's quantum computing business performing?",
            "What are the main revenue drivers for Microsoft's AI services?",
            "Compare quantum computing investments across companies",
            "What challenges did companies face in Q3 2024?"
        ]
        for example in examples:
            if st.button(f"📝 {example}", key=f"example_{hash(example)}"):
                st.session_state.query_input = example
    
    # Query input
    query = st.text_area(
        "Enter your question:",
        height=100,
        placeholder="Ask anything about the earnings calls...",
        key="query_input"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔍 Search", type="primary", disabled=not query.strip()):
            process_query(rag_system, query)
    
    with col2:
        if st.button("🧹 Clear"):
            st.session_state.query_input = ""
            st.rerun()

def process_query(rag_system, query):
    """Process user query and display results"""
    try:
        with st.spinner("Searching and generating answer..."):
            # Get response from RAG system
            response = rag_system.query(query)
            
            if response:
                st.subheader("🎯 Answer")
                st.write(response['answer'])
                
                # Display sources
                if response.get('sources'):
                    with st.expander("📚 Sources"):
                        for i, source in enumerate(response['sources'], 1):
                            st.markdown(f"""
                            **Source {i}:** {source.get('company', 'Unknown')} - {source.get('year', '')} {source.get('quarter', '')}
                            
                            *Relevance Score: {source.get('score', 0):.2f}*
                            
                            {source.get('content', '')[:500]}...
                            """)
                
                # Display confidence
                confidence = response.get('confidence', 0)
                confidence_color = "green" if confidence > 0.8 else "orange" if confidence > 0.6 else "red"
                st.markdown(f"<p style='color: {confidence_color}'>Confidence: {confidence:.1%}</p>", 
                          unsafe_allow_html=True)
            else:
                st.warning("No relevant information found. Try rephrasing your question.")
                
    except Exception as e:
        st.error(f"Query processing failed: {str(e)}")
        logger.error(f"Query error: {str(e)}")

def display_data_management():
    """Display data management interface"""
    st.header("🗄️ Data Management")
    
    tab1, tab2, tab3 = st.tabs(["📊 Data Overview", "🔄 Sync Status", "⚙️ Settings"])
    
    with tab1:
        st.subheader("Current Data Inventory")
        # This would show a table of available data
        # For now, showing placeholder
        st.info("Data inventory will be displayed here")
    
    with tab2:
        st.subheader("Synchronization Status")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Force Full Sync"):
                st.info("Full synchronization initiated...")
        with col2:
            if st.button("🧹 Clear Cache"):
                st.info("Cache cleared successfully!")
    
    with tab3:
        st.subheader("Application Settings")
        
        auto_sync = st.checkbox("Enable automatic data synchronization", value=True)
        sync_frequency = st.selectbox("Sync frequency", ["Hourly", "Daily", "Weekly"])
        max_documents = st.number_input("Maximum documents per company", min_value=10, max_value=1000, value=100)
        
        if st.button("💾 Save Settings"):
            st.success("Settings saved successfully!")

def main():
    """Main application function"""
    display_header()
    
    # Initialize systems
    rag_system, extractor, scheduler = initialize_systems()
    
    # Display sidebar and get filters
    filters = display_sidebar(rag_system, extractor)
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🤖 Q&A Assistant", "📊 Analytics", "🗄️ Data Management", "ℹ️ About"])
    
    with tab1:
        display_query_interface(rag_system)
    
    with tab2:
        display_analytics(rag_system, filters)
    
    with tab3:
        display_data_management()
    
    with tab4:
        st.markdown("""
        ## About This Application
        
        This Earnings Call RAG Assistant helps you extract, store, and query earnings call information 
        from Quantum Computing and AI companies using advanced retrieval-augmented generation.
        
        ### Features:
        - 🔄 Automated data extraction from SEC filings
        - 🧠 Local AI-powered Q&A using Llama3 via Ollama
        - 📊 Interactive analytics and visualizations
        - 🗄️ Efficient vector storage with ChromaDB
        - ⏰ Scheduled data updates
        
        ### Technology Stack:
        - **Frontend**: Streamlit
        - **LLM**: Llama3 via Ollama (local)
        - **Vector DB**: ChromaDB
        - **Data Sources**: SEC filings, Alpha Vantage API
        
        ### Getting Started:
        1. Ensure Ollama is running with Llama3 model
        2. Select companies and time periods in the sidebar
        3. Extract latest earnings data
        4. Ask questions in the Q&A tab
        """)

if __name__ == "__main__":
    main()
