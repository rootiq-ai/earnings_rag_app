"""
Utility functions for the Earnings Call RAG Application
"""

import os
import logging
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

from config import *

def setup_logging() -> logging.Logger:
    """Setup logging configuration"""
    
    # Create logs directory if it doesn't exist
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # Get logger
    logger = logging.getLogger(__name__)
    logger.info("Logging setup completed")
    
    return logger

def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amounts"""
    try:
        if abs(amount) >= 1e9:
            return f"${amount/1e9:.1f}B {currency}"
        elif abs(amount) >= 1e6:
            return f"${amount/1e6:.1f}M {currency}"
        elif abs(amount) >= 1e3:
            return f"${amount/1e3:.1f}K {currency}"
        else:
            return f"${amount:.2f} {currency}"
    except:
        return "N/A"

def format_percentage(value: float, decimal_places: int = 1) -> str:
    """Format percentage values"""
    try:
        return f"{value:.{decimal_places}f}%"
    except:
        return "N/A"

def calculate_metrics(data: Dict[str, Any]) -> Dict[str, float]:
    """Calculate financial metrics from earnings data"""
    metrics = {}
    
    try:
        # Example metric calculations
        revenue = data.get('revenue', 0)
        expenses = data.get('expenses', 0)
        shares = data.get('shares_outstanding', 1)
        
        metrics['profit_margin'] = ((revenue - expenses) / revenue * 100) if revenue > 0 else 0
        metrics['eps'] = (revenue - expenses) / shares if shares > 0 else 0
        metrics['revenue_growth'] = data.get('revenue_growth', 0)
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error calculating metrics: {str(e)}")
    
    return metrics

def clean_text(text: str) -> str:
    """Clean and normalize text content"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)
    
    # Remove extra periods
    text = re.sub(r'\.{2,}', '.', text)
    
    return text.strip()

def extract_financial_figures(text: str) -> List[Dict[str, Any]]:
    """Extract financial figures from text"""
    figures = []
    
    # Patterns for different financial figures
    patterns = {
        'revenue': r'revenue[:\s]+\$?([\d,\.]+)\s*(billion|million|thousand|B|M|K)?',
        'earnings': r'earnings[:\s]+\$?([\d,\.]+)\s*(billion|million|thousand|B|M|K)?',
        'eps': r'eps[:\s]+\$?([\d,\.]+)',
        'growth': r'growth[:\s]+([\d,\.]+)%?'
    }
    
    for metric, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                value = match[0]
                unit = match[1] if len(match) > 1 else ''
            else:
                value = match
                unit = ''
            
            try:
                # Convert to float
                numeric_value = float(value.replace(',', ''))
                
                # Apply unit multiplier
                if unit.upper() in ['BILLION', 'B']:
                    numeric_value *= 1e9
                elif unit.upper() in ['MILLION', 'M']:
                    numeric_value *= 1e6
                elif unit.upper() in ['THOUSAND', 'K']:
                    numeric_value *= 1e3
                
                figures.append({
                    'metric': metric,
                    'value': numeric_value,
                    'original_text': f"{value} {unit}".strip(),
                    'unit': unit
                })
            except ValueError:
                continue
    
    return figures

def parse_quarter_year(quarter_str: str) -> tuple:
    """Parse quarter and year from string"""
    # Patterns like "Q1 2024", "2024 Q1", etc.
    patterns = [
        r'(Q[1-4])\s+(\d{4})',
        r'(\d{4})\s+(Q[1-4])',
        r'(Q[1-4])-(\d{4})',
        r'(\d{4})-(Q[1-4])'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, quarter_str, re.IGNORECASE)
        if match:
            groups = match.groups()
            quarter = next((g for g in groups if g.startswith('Q')), None)
            year = next((g for g in groups if g.isdigit() and len(g) == 4), None)
            return quarter, year
    
    return None, None

def validate_company_ticker(ticker: str) -> bool:
    """Validate if ticker is in supported companies"""
    return ticker.upper() in COMPANIES

def get_company_info(ticker: str) -> Dict[str, str]:
    """Get company information"""
    return COMPANIES.get(ticker.upper(), {
        "name": ticker,
        "sector": "Unknown"
    })

def calculate_quarter_dates(year: str, quarter: str) -> Dict[str, str]:
    """Calculate start and end dates for a quarter"""
    try:
        year_int = int(year)
        
        quarter_months = {
            'Q1': (1, 3),
            'Q2': (4, 6),
            'Q3': (7, 9),
            'Q4': (10, 12)
        }
        
        if quarter not in quarter_months:
            return {}
        
        start_month, end_month = quarter_months[quarter]
        
        start_date = datetime(year_int, start_month, 1)
        
        # Calculate last day of quarter
        if end_month == 12:
            end_date = datetime(year_int + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year_int, end_month + 1, 1) - timedelta(days=1)
        
        return {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'quarter': quarter,
            'year': year
        }
        
    except Exception:
        return {}

def generate_report_summary(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary statistics for a report"""
    if not data:
        return {}
    
    summary = {
        'total_documents': len(data),
        'companies': set(),
        'years': set(),
        'quarters': set(),
        'date_range': {'start': None, 'end': None}
    }
    
    dates = []
    
    for item in data:
        # Extract metadata
        metadata = item.get('metadata', {})
        
        summary['companies'].add(metadata.get('company', 'Unknown'))
        summary['years'].add(metadata.get('year', 'Unknown'))
        summary['quarters'].add(metadata.get('quarter', 'Unknown'))
        
        # Track dates
        date_str = metadata.get('date', '')
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                dates.append(date_obj)
            except:
                pass
    
    # Calculate date range
    if dates:
        summary['date_range']['start'] = min(dates).strftime('%Y-%m-%d')
        summary['date_range']['end'] = max(dates).strftime('%Y-%m-%d')
    
    # Convert sets to sorted lists
    summary['companies'] = sorted(list(summary['companies']))
    summary['years'] = sorted(list(summary['years']))
    summary['quarters'] = sorted(list(summary['quarters']))
    
    return summary

def export_data_to_csv(data: List[Dict[str, Any]], filename: str) -> bool:
    """Export data to CSV format"""
    try:
        # Flatten the data for CSV export
        flattened_data = []
        
        for item in data:
            flat_item = {}
            
            # Basic fields
            flat_item['content'] = item.get('content', '')[:500] + '...' if len(item.get('content', '')) > 500 else item.get('content', '')
            flat_item['source'] = item.get('source', '')
            flat_item['date'] = item.get('date', '')
            
            # Metadata fields
            metadata = item.get('metadata', {})
            flat_item['company'] = metadata.get('company', '')
            flat_item['year'] = metadata.get('year', '')
            flat_item['quarter'] = metadata.get('quarter', '')
            flat_item['sector'] = get_company_info(metadata.get('company', '')).get('sector', '')
            
            flattened_data.append(flat_item)
        
        # Create DataFrame and export
        df = pd.DataFrame(flattened_data)
        filepath = os.path.join(PROCESSED_DATA_DIR, filename)
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        logging.getLogger(__name__).info(f"Data exported to {filepath}")
        return True
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to export data: {str(e)}")
        return False

def create_backup(source_dir: str, backup_name: str) -> bool:
    """Create backup of data directory"""
    try:
        import shutil
        
        backup_dir = os.path.join(DATA_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_path = os.path.join(backup_dir, f"{backup_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        shutil.copytree(source_dir, backup_path)
        
        logging.getLogger(__name__).info(f"Backup created at {backup_path}")
        return True
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Backup failed: {str(e)}")
        return False

def check_system_health() -> Dict[str, Any]:
    """Check system health and return status"""
    health_status = {
        'timestamp': datetime.now().isoformat(),
        'directories': {},
        'disk_space': {},
        'logs': {}
    }
    
    # Check directories
    required_dirs = [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, CHROMA_DB_DIR, LOGS_DIR]
    
    for directory in required_dirs:
        health_status['directories'][directory] = {
            'exists': os.path.exists(directory),
            'writable': os.access(directory, os.W_OK) if os.path.exists(directory) else False
        }
    
    # Check disk space
    try:
        import shutil
        total, used, free = shutil.disk_usage(DATA_DIR)
        health_status['disk_space'] = {
            'total_gb': total // (1024**3),
            'used_gb': used // (1024**3),
            'free_gb': free // (1024**3),
            'usage_percent': (used / total) * 100
        }
    except Exception:
        health_status['disk_space'] = {'error': 'Could not determine disk usage'}
    
    # Check log file
    try:
        if os.path.exists(LOG_FILE):
            stat = os.stat(LOG_FILE)
            health_status['logs'] = {
                'size_mb': stat.st_size // (1024**2),
                'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
    except Exception:
        health_status['logs'] = {'error': 'Could not access log file'}
    
    return health_status

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove extra spaces and underscores
    sanitized = re.sub(r'[_\s]+', '_', sanitized)
    
    # Ensure reasonable length
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    
    return sanitized.strip('_')

def load_json_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Safely load JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to load JSON file {filepath}: {str(e)}")
        return None

def save_json_file(data: Dict[str, Any], filepath: str) -> bool:
    """Safely save JSON file"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to save JSON file {filepath}: {str(e)}")
        return False
