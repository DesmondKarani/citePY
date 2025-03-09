"""
Configuration module for the citation generator.

This module loads configuration from environment variables and provides
default values for various settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# API configurations
API_KEYS = {
    'isbndb': os.getenv('ISBNDB_API_KEY', ''),
}

# Citation styles directory
STYLES_DIR = os.path.join(BASE_DIR, 'styles')

# Server configuration
PORT = int(os.getenv('PORT', 8000))
HOST = os.getenv('HOST', '0.0.0.0')
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Cache configuration
CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'True').lower() in ('true', '1', 't')
CACHE_MAX_SIZE = int(os.getenv('CACHE_MAX_SIZE', 1000))
CACHE_TTL = int(os.getenv('CACHE_TTL', 86400))  # 24 hours in seconds

# Rate limiting
RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'True').lower() in ('true', '1', 't')
RATE_LIMIT = int(os.getenv('RATE_LIMIT', 100))  # requests per hour

# Update API keys in the data fetcher configuration
def configure_api_keys():
    """Update API configuration with keys from environment variables."""
    from data_fetcher import API_CONFIG
    
    if API_KEYS['isbndb']:
        if 'isbndb' in API_CONFIG:
            API_CONFIG['isbndb']['headers']['Authorization'] = API_KEYS['isbndb']
