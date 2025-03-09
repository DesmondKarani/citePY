"""
CSL Converter Module

This module handles conversion of raw metadata from various sources
into Citation Style Language (CSL) JSON format.
"""

import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

def convert_to_csl_json(metadata):
    """
    Convert raw metadata from various sources into CSL JSON format.
    
    Args:
        metadata (dict): Raw metadata from various sources
        
    Returns:
        dict: Metadata in CSL JSON format
    """
    identifier_type = metadata.get('identifier_type')
    
    if identifier_type == 'doi':
        return convert_doi_metadata_to_csl(metadata)
    elif identifier_type == 'isbn':
        return convert_isbn_metadata_to_csl(metadata)
    else:
        # Create a minimal CSL JSON record
        return {
            'id': metadata.get('identifier', 'unknown'),
            'type': 'article',
            'title': metadata.get('title', 'Unknown Title')
        }

def convert_doi_metadata_to_csl(metadata):
    """
    Convert DOI metadata to CSL JSON format.
    
    Args:
        metadata (dict): Raw DOI metadata from various sources
        
    Returns:
        dict: DOI metadata in CSL JSON format
    """
    csl = {}
    
    # Set the ID (always the DOI)
    csl['id'] = metadata.get('identifier', 'unknown')
    
    # Determine document type
    if 'crossref' in metadata and 'type' in metadata['crossref']:
        csl['type'] = map_crossref_type_to_csl(metadata['crossref']['type'])
    else:
        csl['type'] = 'article-journal'  # Default type for DOIs
    
    # Set the title
    if 'title' in metadata:
        csl['title'] = metadata['title']
    elif 'crossref' in metadata and 'title' in metadata['crossref']:
        csl['title'] = metadata['crossref']['title'][0]
    
    # Set the authors
    if 'authors' in metadata:
        csl['author'] = metadata['authors']
    elif 'crossref' in metadata and 'author' in metadata['crossref']:
        csl['author'] = []
        for author in metadata['crossref']['author']:
            author_entry = {}
            if 'family' in author:
                author_entry['family'] = author['family']
            if 'given' in author:
                author_entry['given'] = author['given']
            csl['author'].append(author_entry)
    
    # Set publication date
    if 'published_date' in metadata:
        csl['issued'] = metadata['published_date']
    elif 'crossref' in metadata:
        if 'published-print' in metadata['crossref']:
            csl['issued'] = metadata['crossref']['published-print']
        elif 'published-online' in metadata['crossref']:
            csl['issued'] = metadata['crossref']['published-online']
        elif 'created' in metadata['crossref']:
            csl['issued'] = metadata['crossref']['created']
    
    # Set the publisher
    if 'publisher' in metadata:
        csl['publisher'] = metadata['publisher']
    elif 'crossref' in metadata and 'publisher' in metadata['crossref']:
        csl['publisher'] = metadata['crossref']['publisher']
    
    # Set the container title (journal name)
    if 'crossref' in metadata and 'container-title' in metadata['crossref']:
        csl['container-title'] = metadata['crossref']['container-title'][0] if metadata['crossref']['container-title'] else ""
    
    # Set volume, issue, and page numbers
    if 'crossref' in metadata:
        if 'volume' in metadata['crossref']:
            csl['volume'] = metadata['crossref']['volume']
        if 'issue' in metadata['crossref']:
            csl['issue'] = metadata['crossref']['issue']
        if 'page' in metadata['crossref']:
            csl['page'] = metadata['crossref']['page']
    
    # Set the URL
    csl['URL'] = f"https://doi.org/{metadata['identifier']}"
    
    # Set open access URL if available
    if 'open_access_url' in metadata:
        csl['URL'] = metadata['open_access_url']
    
    # Set the DOI
    csl['DOI'] = metadata['identifier']
    
    # Set ISSN if available
    if 'crossref' in metadata and 'ISSN' in metadata['crossref']:
        csl['ISSN'] = metadata['crossref']['ISSN'][0] if metadata['crossref']['ISSN'] else ""
    
    # Set abstract if available
    if 'crossref' in metadata and 'abstract' in metadata['crossref']:
        csl['abstract'] = metadata['crossref']['abstract']
    
    return csl

def convert_isbn_metadata_to_csl(metadata):
    """
    Convert ISBN metadata to CSL JSON format.
    
    Args:
        metadata (dict): Raw ISBN metadata from various sources
        
    Returns:
        dict: ISBN metadata in CSL JSON format
    """
    csl = {}
    
    # Set the ID (ISBN)
    csl['id'] = metadata.get('identifier', 'unknown')
    
    # Books have a fixed type
    csl['type'] = 'book'
    
    # Set the title
    if 'title' in metadata:
        csl['title'] = metadata['title']
    
    # Set the authors
    if 'authors' in metadata:
        csl['author'] = metadata['authors']
    
    # Set publication date
    if 'published_date' in metadata:
        csl['issued'] = metadata['published_date']
    
    # Set the publisher
    if 'publisher' in metadata:
        csl['publisher'] = metadata['publisher']
    
    # Set number of pages
    if 'page_count' in metadata:
        csl['number-of-pages'] = metadata['page_count']
    
    # Set edition if available
    if 'openlibrary' in metadata and 'edition_name' in metadata['openlibrary']:
        edition = metadata['openlibrary']['edition_name']
        edition_match = re.search(r'(\d+)\w*\s+edition', edition, re.IGNORECASE)
        if edition_match:
            csl['edition'] = edition_match.group(1)
    elif 'google_books' in metadata and 'edition' in metadata['google_books']:
        edition = metadata['google_books']['edition']
        edition_match = re.search(r'(\d+)', edition)
        if edition_match:
            csl['edition'] = edition_match.group(1)
    
    # Set the ISBN
    csl['ISBN'] = metadata['identifier']
    
    # Set the URL
    if 'openlibrary' in metadata and 'url' in metadata['openlibrary']:
        csl['URL'] = metadata['openlibrary']['url']
    elif 'google_books' in metadata and 'infoLink' in metadata['google_books']:
        csl['URL'] = metadata['google_books']['infoLink']
    
    # Set the place (publisher location)
    if 'openlibrary' in metadata and 'publish_places' in metadata['openlibrary'] and metadata['openlibrary']['publish_places']:
        csl['publisher-place'] = metadata['openlibrary']['publish_places'][0]['name']
    
    return csl

def map_crossref_type_to_csl(crossref_type):
    """
    Map Crossref document types to CSL types.
    
    Args:
        crossref_type (str): Crossref document type
        
    Returns:
        str: Corresponding CSL document type
    """
    type_mapping = {
        'journal-article': 'article-journal',
        'book-chapter': 'chapter',
        'book': 'book',
        'monograph': 'book',
        'edited-book': 'book',
        'reference-book': 'book',
        'proceedings-article': 'paper-conference',
        'proceedings': 'paper-conference',
        'conference-paper': 'paper-conference',
        'report': 'report',
        'report-series': 'report',
        'standard': 'report',
        'dissertation': 'thesis',
        'dataset': 'dataset',
        'posted-content': 'post',
        'journal-issue': 'article-journal',
        'journal-volume': 'article-journal',
        'journal': 'article-journal',
        'book-series': 'book',
        'book-set': 'book',
        'book-track': 'chapter',
        'book-part': 'chapter',
        'book-section': 'chapter',
        'proceedings-series': 'paper-conference',
        'report-component': 'report',
        'standard-series': 'report'
    }
    
    return type_mapping.get(crossref_type, 'article-journal')
