"""
Citation Data Fetcher

This module handles fetching citation metadata from various APIs
based on DOIs, ISBNs, and other identifiers.
"""

import requests
import logging
import re
import json
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# API URLs and configuration
API_CONFIG = {
    'crossref': {
        'url': 'https://api.crossref.org/works/',
        'headers': {
            'User-Agent': 'CitationGenerator/1.0 (mailto:support@citationgenerator.com)'
        }
    },
    'datacite': {
        'url': 'https://api.datacite.org/dois/'
    },
    'openlibrary': {
        'url': 'https://openlibrary.org/api/books'
    },
    'worldcat': {
        'url': 'http://xisbn.worldcat.org/webservices/xid/isbn/'
    },
    'unpaywall': {
        'url': 'https://api.unpaywall.org/v2/',
        'params': {
            'email': 'support@citationgenerator.com'
        }
    },
    'google_books': {
        'url': 'https://www.googleapis.com/books/v1/volumes'
    },
    'isbndb': {
        'url': 'https://api.isbndb.com/book/',
        'headers': {
            'Authorization': 'YOUR_ISBNDB_API_KEY'  # Replace with actual key when available
        }
    }
}

# Validation patterns
DOI_PATTERN = r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$"
ISBN_10_PATTERN = r"^\d{9}[\dX]$"
ISBN_13_PATTERN = r"^\d{13}$"

def clean_identifier(identifier):
    """
    Clean and normalize an identifier (DOI or ISBN).
    
    Args:
        identifier (str): The identifier to clean
        
    Returns:
        str: Cleaned identifier
    """
    # Remove any http/https prefix for DOIs
    if identifier.startswith(('http://', 'https://')):
        if 'doi.org/' in identifier:
            doi_match = re.search(r'doi\.org/(.+)$', identifier)
            if doi_match:
                identifier = doi_match.group(1)
    
    # For ISBNs, remove hyphens and spaces
    if re.match(r'^\d+[-\s]', identifier):
        identifier = re.sub(r'[-\s]', '', identifier)
    
    return identifier.strip()

def is_valid_doi(doi):
    """
    Check if a string is a valid DOI.
    
    Args:
        doi (str): The DOI to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    return bool(re.match(DOI_PATTERN, doi, re.IGNORECASE))

def is_valid_isbn(isbn):
    """
    Check if a string is a valid ISBN-10 or ISBN-13.
    
    Args:
        isbn (str): The ISBN to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Remove any hyphens or spaces
    isbn = re.sub(r'[-\s]', '', isbn)
    
    # Check for ISBN-10
    if len(isbn) == 10:
        if not isbn[:-1].isdigit():
            return False
        if isbn[-1].upper() == 'X' or isbn[-1].isdigit():
            return True
        return False
    
    # Check for ISBN-13
    elif len(isbn) == 13:
        return isbn.isdigit()
    
    return False

def identify_identifier_type(identifier):
    """
    Identify the type of an identifier.
    
    Args:
        identifier (str): The identifier to check
        
    Returns:
        str: 'doi', 'isbn', or None if not recognized
    """
    identifier = clean_identifier(identifier)
    
    if is_valid_doi(identifier):
        return 'doi'
    elif is_valid_isbn(identifier):
        return 'isbn'
    return None

def fetch_from_api(api_name, identifier, additional_params=None):
    """
    Generic function to fetch data from an API.
    
    Args:
        api_name (str): Name of the API to use
        identifier (str): The identifier to look up
        additional_params (dict, optional): Additional parameters for the API request
        
    Returns:
        dict: API response data or None if request failed
    """
    if api_name not in API_CONFIG:
        logger.error(f"Unknown API: {api_name}")
        return None
    
    config = API_CONFIG[api_name]
    url = config['url']
    headers = config.get('headers', {})
    params = config.get('params', {})
    
    # Update with additional parameters
    if additional_params:
        params.update(additional_params)
    
    try:
        # Different APIs have different URL structures
        if api_name == 'crossref' or api_name == 'datacite' or api_name == 'unpaywall':
            full_url = f"{url}{identifier}"
        elif api_name == 'openlibrary':
            full_url = url
            params['bibkeys'] = f"ISBN:{identifier}"
            params['format'] = 'json'
            params['jscmd'] = 'data'
        elif api_name == 'worldcat':
            full_url = f"{url}{identifier}"
            params['method'] = 'getMetadata'
            params['format'] = 'json'
            params['fl'] = '*'
        elif api_name == 'google_books':
            full_url = url
            params['q'] = f"isbn:{identifier}" if is_valid_isbn(identifier) else f"doi:{identifier}"
        elif api_name == 'isbndb':
            full_url = f"{url}{identifier}"
        else:
            full_url = f"{url}{identifier}"
        
        # Make the request
        response = requests.get(full_url, headers=headers, params=params)
        response.raise_for_status()
        
        # Return JSON response
        return response.json()
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from {api_name}: {e}")
        return None
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON response from {api_name}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching from {api_name}: {e}")
        return None

def fetch_doi_metadata(doi):
    """
    Fetch metadata for a DOI from multiple sources.
    
    Args:
        doi (str): The DOI to look up
        
    Returns:
        dict: Combined metadata from various sources
    """
    metadata = {
        'identifier': doi,
        'identifier_type': 'doi',
        'sources': [],
        'retrieved_at': datetime.now().isoformat()
    }
    
    # Try Crossref (primary source for most DOIs)
    crossref_data = fetch_from_api('crossref', doi)
    if crossref_data and 'message' in crossref_data:
        metadata['crossref'] = crossref_data['message']
        metadata['sources'].append('crossref')
        
        # Set some basic fields from Crossref
        if 'title' in crossref_data['message']:
            metadata['title'] = crossref_data['message']['title'][0]
        if 'author' in crossref_data['message']:
            metadata['authors'] = crossref_data['message']['author']
        if 'published-print' in crossref_data['message']:
            metadata['published_date'] = crossref_data['message']['published-print']
        elif 'published-online' in crossref_data['message']:
            metadata['published_date'] = crossref_data['message']['published-online']
        if 'publisher' in crossref_data['message']:
            metadata['publisher'] = crossref_data['message']['publisher']
        if 'type' in crossref_data['message']:
            metadata['type'] = crossref_data['message']['type']
        
    # Try DataCite (good for datasets and alternative DOIs)
    datacite_data = fetch_from_api('datacite', doi)
    if datacite_data and 'data' in datacite_data and 'attributes' in datacite_data['data']:
        metadata['datacite'] = datacite_data['data']['attributes']
        metadata['sources'].append('datacite')
        
        # If we didn't get basic info from Crossref, try from DataCite
        if 'title' not in metadata and 'titles' in datacite_data['data']['attributes']:
            metadata['title'] = datacite_data['data']['attributes']['titles'][0]['title']
        if 'authors' not in metadata and 'creators' in datacite_data['data']['attributes']:
            metadata['authors'] = [{'given': c.get('givenName', ''), 
                                  'family': c.get('familyName', '')} 
                                 for c in datacite_data['data']['attributes']['creators']]
        if 'published_date' not in metadata and 'dates' in datacite_data['data']['attributes']:
            for date in datacite_data['data']['attributes']['dates']:
                if date['dateType'] == 'Issued':
                    year = date['date'][:4]
                    metadata['published_date'] = {'date-parts': [[year]]}
                    break
    
    # Try Unpaywall (for open access information)
    unpaywall_data = fetch_from_api('unpaywall', doi)
    if unpaywall_data:
        metadata['unpaywall'] = unpaywall_data
        metadata['sources'].append('unpaywall')
        
        # Get open access URL if available
        if 'is_oa' in unpaywall_data and unpaywall_data['is_oa']:
            if 'best_oa_location' in unpaywall_data and unpaywall_data['best_oa_location']:
                metadata['open_access_url'] = unpaywall_data['best_oa_location'].get('url')
    
    return metadata

def fetch_isbn_metadata(isbn):
    """
    Fetch metadata for an ISBN from multiple sources.
    
    Args:
        isbn (str): The ISBN to look up
        
    Returns:
        dict: Combined metadata from various sources
    """
    metadata = {
        'identifier': isbn,
        'identifier_type': 'isbn',
        'sources': [],
        'retrieved_at': datetime.now().isoformat()
    }
    
    # Try Open Library (good free source for book data)
    openlibrary_data = fetch_from_api('openlibrary', isbn)
    if openlibrary_data and f"ISBN:{isbn}" in openlibrary_data:
        book_data = openlibrary_data[f"ISBN:{isbn}"]
        metadata['openlibrary'] = book_data
        metadata['sources'].append('openlibrary')
        
        # Set basic fields
        if 'title' in book_data:
            metadata['title'] = book_data['title']
        if 'authors' in book_data:
            metadata['authors'] = [{'family': a.get('name', '').split()[-1] if ' ' in a.get('name', '') else a.get('name', ''),
                                  'given': ' '.join(a.get('name', '').split()[:-1]) if ' ' in a.get('name', '') else ''}
                                 for a in book_data['authors']]
        if 'publishers' in book_data and book_data['publishers']:
            metadata['publisher'] = book_data['publishers'][0]['name']
        if 'publish_date' in book_data:
            # Extract year from publish date
            year_match = re.search(r'\d{4}', book_data['publish_date'])
            if year_match:
                metadata['published_date'] = {'date-parts': [[year_match.group(0)]]}
        if 'number_of_pages' in book_data:
            metadata['page_count'] = book_data['number_of_pages']
    
    # Try Google Books
    google_data = fetch_from_api('google_books', isbn)
    if google_data and 'items' in google_data and google_data['items']:
        book_data = google_data['items'][0]['volumeInfo']
        metadata['google_books'] = book_data
        metadata['sources'].append('google_books')
        
        # Set basic fields if not already set
        if 'title' not in metadata and 'title' in book_data:
            metadata['title'] = book_data['title']
        if 'authors' not in metadata and 'authors' in book_data:
            metadata['authors'] = [{'family': a.split()[-1] if ' ' in a else a,
                                  'given': ' '.join(a.split()[:-1]) if ' ' in a else ''}
                                 for a in book_data['authors']]
        if 'publisher' not in metadata and 'publisher' in book_data:
            metadata['publisher'] = book_data['publisher']
        if 'published_date' not in metadata and 'publishedDate' in book_data:
            year_match = re.search(r'\d{4}', book_data['publishedDate'])
            if year_match:
                metadata['published_date'] = {'date-parts': [[year_match.group(0)]]}
        if 'page_count' not in metadata and 'pageCount' in book_data:
            metadata['page_count'] = book_data['pageCount']
    
    # Try WorldCat (library catalog data)
    worldcat_data = fetch_from_api('worldcat', isbn)
    if worldcat_data and 'list' in worldcat_data and worldcat_data['list']:
        book_data = worldcat_data['list'][0]
        metadata['worldcat'] = book_data
        metadata['sources'].append('worldcat')
        
        # Set basic fields if not already set
        if 'title' not in metadata and 'title' in book_data:
            metadata['title'] = book_data['title']
        if 'authors' not in metadata and 'author' in book_data:
            # WorldCat may return author as a string with multiple authors
            authors = book_data['author'].split(';')
            metadata['authors'] = [{'family': a.strip().split()[-1] if ' ' in a.strip() else a.strip(),
                                  'given': ' '.join(a.strip().split()[:-1]) if ' ' in a.strip() else ''}
                                 for a in authors]
        if 'publisher' not in metadata and 'publisher' in book_data:
            metadata['publisher'] = book_data['publisher']
        if 'published_date' not in metadata and 'year' in book_data:
            metadata['published_date'] = {'date-parts': [[book_data['year']]]}
    
    # Optional: Try ISBNdb if API key is set
    if 'headers' in API_CONFIG['isbndb'] and 'Authorization' in API_CONFIG['isbndb']['headers'] and API_CONFIG['isbndb']['headers']['Authorization'] != 'YOUR_ISBNDB_API_KEY':
        isbndb_data = fetch_from_api('isbndb', isbn)
        if isbndb_data and 'book' in isbndb_data:
            book_data = isbndb_data['book']
            metadata['isbndb'] = book_data
            metadata['sources'].append('isbndb')
            
            # ISBNdb usually has comprehensive data, so we might prefer it
            if 'title' in book_data:
                metadata['title'] = book_data['title']
            if 'authors' in book_data:
                metadata['authors'] = [{'family': a.split()[-1] if ' ' in a else a,
                                      'given': ' '.join(a.split()[:-1]) if ' ' in a else ''}
                                     for a in book_data['authors']]
            if 'publisher' in book_data:
                metadata['publisher'] = book_data['publisher']
            if 'date_published' in book_data:
                year_match = re.search(r'\d{4}', book_data['date_published'])
                if year_match:
                    metadata['published_date'] = {'date-parts': [[year_match.group(0)]]}
            if 'pages' in book_data:
                metadata['page_count'] = book_data['pages']
    
    # Set a default type for ISBN records
    metadata['type'] = 'book'
    
    return metadata

def fetch_metadata(identifier):
    """
    Fetch metadata for a DOI or ISBN from multiple sources.
    
    Args:
        identifier (str): The DOI or ISBN to look up
        
    Returns:
        dict: Combined metadata from various sources
    """
    # Clean the identifier
    identifier = clean_identifier(identifier)
    
    # Determine identifier type
    identifier_type = identify_identifier_type(identifier)
    
    if identifier_type == 'doi':
        return fetch_doi_metadata(identifier)
    elif identifier_type == 'isbn':
        return fetch_isbn_metadata(identifier)
    else:
        return {
            'identifier': identifier,
            'identifier_type': 'unknown',
            'error': 'Unrecognized identifier format',
            'retrieved_at': datetime.now().isoformat()
        }
