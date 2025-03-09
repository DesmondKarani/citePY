"""
Citation Styles Utility

This module provides utility functions for handling citation styles and formatting.
It uses the Citation Style Language (CSL) to generate properly formatted citations.
"""

import os
import json
import requests
import logging
from citeproc_py.style import CitationStylesStyle
from citeproc_py.source import CiteProcJSON
from citeproc_py.formatter.html import HtmlFormatter
from citeproc_py.formatter.plain import PlainFormatter
from citeproc_py.citation import CitationItem

# Directory for storing CSL style files
STYLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'styles')
os.makedirs(STYLES_DIR, exist_ok=True)

# Citation style mapping (style name to CSL style ID)
STYLE_MAPPING = {
    'apa': 'apa',
    'apa-7th': 'apa-7',
    'mla': 'modern-language-association',
    'mla-9': 'modern-language-association-9',
    'chicago': 'chicago-author-date',
    'chicago-notes': 'chicago-note-bibliography',
    'harvard': 'harvard-cite-them-right',
    'ieee': 'ieee',
    'vancouver': 'vancouver',
    'ama': 'american-medical-association',
    'acs': 'american-chemical-society',
    'nature': 'nature',
    'science': 'science',
    'bibtex': 'bibtex',
    'acm': 'acm-sig-proceedings'
}

logger = logging.getLogger(__name__)

def download_csl_style(style_id):
    """
    Download a CSL style file from the CSL repository if not already cached.
    
    Args:
        style_id (str): The identifier for the CSL style
        
    Returns:
        str: Path to the downloaded style file
    """
    style_path = os.path.join(STYLES_DIR, f"{style_id}.csl")
    
    # Only download if we don't have it cached
    if not os.path.exists(style_path):
        try:
            # Try to download from the GitHub CSL styles repository
            url = f"https://raw.githubusercontent.com/citation-style-language/styles/master/{style_id}.csl"
            response = requests.get(url)
            response.raise_for_status()
            
            with open(style_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
                
            logger.info(f"Downloaded style: {style_id}")
        except Exception as e:
            logger.error(f"Error downloading style {style_id}: {e}")
            return None
    
    return style_path

def get_all_available_styles():
    """
    Return a dictionary of all available citation styles.
    
    Returns:
        dict: A dictionary mapping style names to their descriptions
    """
    return {
        'apa': 'APA 6th Edition',
        'apa-7th': 'APA 7th Edition',
        'mla': 'MLA 8th Edition',
        'mla-9': 'MLA 9th Edition',
        'chicago': 'Chicago Author-Date',
        'chicago-notes': 'Chicago Notes and Bibliography',
        'harvard': 'Harvard Reference Format',
        'ieee': 'IEEE',
        'vancouver': 'Vancouver',
        'ama': 'American Medical Association',
        'acs': 'American Chemical Society',
        'nature': 'Nature Journal',
        'science': 'Science Magazine',
        'bibtex': 'BibTeX',
        'acm': 'Association for Computing Machinery'
    }

def format_citation(csl_data, style_name, output_format='plain'):
    """
    Format a citation using the specified style.
    
    Args:
        csl_data (dict): Citation data in CSL-JSON format
        style_name (str): Name of the citation style
        output_format (str): Output format ('plain' or 'html')
        
    Returns:
        str: Formatted citation
    """
    # Get the CSL style ID from the mapping
    style_id = STYLE_MAPPING.get(style_name.lower(), 'apa')
    
    # Download/get the style file
    style_path = download_csl_style(style_id)
    
    if not style_path:
        logger.error(f"Style not found: {style_name}")
        return f"Error: Style '{style_name}' not found."
    
    try:
        # Load the style file
        with open(style_path, 'r', encoding='utf-8') as f:
            style_content = f.read()
        
        # Create a CiteProcJSON source from the CSL data
        # Ensure csl_data is a list if it's a single citation
        if not isinstance(csl_data, list):
            csl_data = [csl_data]
            
        # Ensure each item has an ID
        for i, item in enumerate(csl_data):
            if 'id' not in item:
                item['id'] = f"item-{i}"
                
        source = CiteProcJSON(csl_data)
        
        # Create the style
        style = CitationStylesStyle(style_content)
        
        # Choose formatter
        formatter = PlainFormatter() if output_format == 'plain' else HtmlFormatter()
        
        # Create the citation processor
        from citeproc_py.citation import CitationStylesBibliography
        bibliography = CitationStylesBibliography(style, source, formatter)
        
        # Process all items
        for item in csl_data:
            citation = [CitationItem(item['id'])]
            bibliography.register(citation)
        
        # Generate the bibliography
        bibliography.sort()
        bibliography.update_items()
        
        # Return the formatted bibliography
        return str(bibliography.bibliography())
    
    except Exception as e:
        logger.error(f"Error formatting citation: {e}")
        return f"Error formatting citation: {str(e)}"

def generate_parenthetical_citation(csl_data, style_name):
    """
    Generate a parenthetical in-text citation.
    
    Args:
        csl_data (dict): Citation data in CSL-JSON format
        style_name (str): Name of the citation style
        
    Returns:
        str: Parenthetical citation text
    """
    style_name = style_name.lower()
    
    try:
        # Extract author information
        authors = csl_data.get('author', [])
        author_text = ""
        
        if authors:
            if len(authors) == 1:
                author_text = authors[0].get('family', '')
            elif len(authors) == 2:
                author_text = f"{authors[0].get('family', '')} & {authors[1].get('family', '')}"
            else:
                author_text = f"{authors[0].get('family', '')} et al."
        
        # Extract year
        year = ""
        if 'issued' in csl_data:
            date_parts = csl_data['issued'].get('date-parts', [['']])
            if date_parts and date_parts[0]:
                year = date_parts[0][0]
        
        # Format based on style
        if style_name in ['apa', 'apa-7th', 'harvard']:
            if author_text and year:
                return f"({author_text}, {year})"
            elif author_text:
                return f"({author_text})"
            elif year:
                return f"({year})"
                
        elif style_name in ['mla', 'mla-9']:
            if author_text:
                return f"({author_text})"
                
        elif style_name in ['chicago', 'chicago-notes']:
            if author_text and year:
                return f"({author_text} {year})"
                
        elif style_name == 'ieee':
            # IEEE uses numbered citations
            return f"[{csl_data.get('id', '?')}]"
            
        # Default format if we don't have specific rules
        if author_text and year:
            return f"({author_text}, {year})"
        elif author_text:
            return f"({author_text})"
        elif year:
            return f"({year})"
        
        # Last resort
        return f"({csl_data.get('id', '?')})"
            
    except Exception as e:
        logger.error(f"Error generating parenthetical citation: {e}")
        return f"(Citation Error)"

def generate_narrative_citation(csl_data, style_name):
    """
    Generate a narrative in-text citation.
    
    Args:
        csl_data (dict): Citation data in CSL-JSON format
        style_name (str): Name of the citation style
        
    Returns:
        str: Narrative citation text
    """
    style_name = style_name.lower()
    
    try:
        # Extract author information
        authors = csl_data.get('author', [])
        author_text = ""
        
        if authors:
            if len(authors) == 1:
                author_text = authors[0].get('family', '')
            elif len(authors) == 2:
                author_text = f"{authors[0].get('family', '')} and {authors[1].get('family', '')}"
            else:
                author_text = f"{authors[0].get('family', '')} et al."
        
        # Extract year
        year = ""
        if 'issued' in csl_data:
            date_parts = csl_data['issued'].get('date-parts', [['']])
            if date_parts and date_parts[0]:
                year = date_parts[0][0]
        
        # Format based on style
        if style_name in ['apa', 'apa-7th', 'harvard']:
            if author_text and year:
                return f"{author_text} ({year})"
            elif author_text:
                return author_text
            elif year:
                return f"({year})"
                
        elif style_name in ['mla', 'mla-9']:
            if author_text:
                return author_text
                
        elif style_name in ['chicago', 'chicago-notes']:
            if author_text and year:
                return f"{author_text} ({year})"
                
        elif style_name == 'ieee':
            # IEEE uses numbered citations
            return f"[{csl_data.get('id', '?')}]"
            
        # Default format if we don't have specific rules
        if author_text and year:
            return f"{author_text} ({year})"
        elif author_text:
            return author_text
        elif year:
            return f"({year})"
        
        # Last resort
        return csl_data.get('id', '?')
            
    except Exception as e:
        logger.error(f"Error generating narrative citation: {e}")
        return "Citation Error"
