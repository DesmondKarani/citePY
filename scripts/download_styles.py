#!/usr/bin/env python
"""
Download Citation Style Language (CSL) files from the GitHub repository.

This script downloads the required CSL style files for the citation generator.
"""

import os
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create styles directory in the app folder
# Go up one level to the project root, then into app/styles
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
STYLES_DIR = os.path.join(PROJECT_ROOT, 'app', 'styles')
os.makedirs(STYLES_DIR, exist_ok=True)

# List of CSL styles to download
STYLES = [
    'apa',
    'apa-7',  # Corrected from apa-7th-edition
    'modern-language-association',
    'modern-language-association-9',  # Corrected
    'chicago-author-date',
    'chicago-note-bibliography',
    'harvard-cite-them-right',  # Corrected from harvard1
    'ieee',
    'vancouver',
    'american-medical-association',
    'american-chemical-society',
    'nature',
    'science',
    'bibtex',
    'acm-sig-proceedings'  # Corrected from association-for-computing-machinery
]

# GitHub repository URL for CSL styles
CSL_REPO_URL = "https://raw.githubusercontent.com/citation-style-language/styles/master/"

def download_style(style_id):
    """
    Download a CSL style file from the GitHub repository.
    
    Args:
        style_id (str): The style identifier
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        style_url = f"{CSL_REPO_URL}{style_id}.csl"
        response = requests.get(style_url)
        response.raise_for_status()
        
        style_path = os.path.join(STYLES_DIR, f"{style_id}.csl")
        with open(style_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
            
        logger.info(f"Downloaded {style_id}.csl")
        return True
    except Exception as e:
        logger.error(f"Failed to download {style_id}.csl: {e}")
        return False

def main():
    """Main function to download all CSL style files."""
    logger.info(f"Downloading {len(STYLES)} CSL style files to {STYLES_DIR}")
    
    success_count = 0
    for style in STYLES:
        if download_style(style):
            success_count += 1
    
    logger.info(f"Successfully downloaded {success_count} of {len(STYLES)} CSL style files")

if __name__ == "__main__":
    main()
