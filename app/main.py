"""
Citation Generator API

A FastAPI application that serves as the backend for the citation generator.
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import json
from datetime import datetime
import uvicorn

# Import our modules
from app.data_fetcher import fetch_metadata, clean_identifier, identify_identifier_type
from app.csl_converter import convert_to_csl_json
from app.citation_styles import format_citation, generate_parenthetical_citation, generate_narrative_citation, get_all_available_styles

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Citation Generator API",
    description="API for generating citations from DOIs and ISBNs",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class IdentifierRequest(BaseModel):
    identifier: str = Field(..., description="DOI or ISBN to generate citation for")
    style: str = Field("apa", description="Citation style to use")

class CitationResponse(BaseModel):
    identifier: str = Field(..., description="The input identifier (DOI or ISBN)")
    identifier_type: str = Field(..., description="Type of identifier (doi, isbn)")
    style: str = Field(..., description="Citation style used")
    full_citation: str = Field(..., description="Formatted full citation")
    parenthetical: str = Field(..., description="Parenthetical in-text citation")
    narrative: str = Field(..., description="Narrative in-text citation")
    timestamp: str = Field(..., description="Timestamp of when citation was generated")

class ValidationResponse(BaseModel):
    identifier: str = Field(..., description="The input identifier")
    valid: bool = Field(..., description="Whether the identifier is valid")
    type: Optional[str] = Field(None, description="Type of identifier (doi, isbn) if valid")
    error: Optional[str] = Field(None, description="Error message if invalid")

class StylesResponse(BaseModel):
    styles: Dict[str, str] = Field(..., description="Available citation styles")

# In-memory cache for citation results
citation_cache = {}

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Citation Generator API"}

@app.post("/api/validate", response_model=ValidationResponse)
async def validate_identifier(request: IdentifierRequest):
    """
    Validate a DOI or ISBN.
    """
    identifier = clean_identifier(request.identifier)
    identifier_type = identify_identifier_type(identifier)
    
    if identifier_type:
        return {
            "identifier": identifier,
            "valid": True,
            "type": identifier_type,
            "error": None
        }
    else:
        return {
            "identifier": identifier,
            "valid": False,
            "type": None,
            "error": "Invalid DOI or ISBN format"
        }

@app.post("/api/generate_citation", response_model=CitationResponse)
async def generate_citation(request: IdentifierRequest):
    """
    Generate a citation from a DOI or ISBN.
    """
    identifier = clean_identifier(request.identifier)
    style = request.style.lower()
    
    # Check cache first (only if style is the same)
    cache_key = f"{identifier}:{style}"
    if cache_key in citation_cache:
        return citation_cache[cache_key]
    
    # Validate identifier
    identifier_type = identify_identifier_type(identifier)
    if not identifier_type:
        raise HTTPException(status_code=400, detail="Invalid DOI or ISBN format")
    
    # Fetch metadata
    logger.info(f"Fetching metadata for {identifier_type}: {identifier}")
    metadata = fetch_metadata(identifier)
    
    if not metadata or (identifier_type == 'doi' and 'crossref' not in metadata and 'datacite' not in metadata) or (identifier_type == 'isbn' and 'openlibrary' not in metadata and 'google_books' not in metadata and 'worldcat' not in metadata):
        raise HTTPException(status_code=404, detail=f"Could not find metadata for {identifier_type}: {identifier}")
    
    # Convert to CSL
    csl_data = convert_to_csl_json(metadata)
    
    # Generate citations
    full_citation = format_citation(csl_data, style)
    parenthetical = generate_parenthetical_citation(csl_data, style)
    narrative = generate_narrative_citation(csl_data, style)
    
    # Prepare response
    response = {
        "identifier": identifier,
        "identifier_type": identifier_type,
        "style": style,
        "full_citation": full_citation,
        "parenthetical": parenthetical,
        "narrative": narrative,
        "timestamp": datetime.now().isoformat()
    }
    
    # Cache the result
    citation_cache[cache_key] = response
    
    return response

@app.get("/api/citation_styles", response_model=StylesResponse)
async def get_citation_styles():
    """
    Get available citation styles.
    """
    return {"styles": get_all_available_styles()}

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
