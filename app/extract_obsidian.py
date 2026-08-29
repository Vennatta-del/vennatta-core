"""Obsidian vault extraction endpoint with x402 payment."""

import os
import json
from pathlib import Path
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class ObsidianExtractRequest(BaseModel):
    """Request model for Obsidian extraction."""
    note_path: str  # Path to note in vault
    vault_root: str = "C:/ObsidianVault_Direct"  # Default vault location
    extract_links: bool = True
    extract_tags: bool = True

class ObsidianExtractResponse(BaseModel):
    """Response model for Obsidian extraction."""
    content: str
    metadata: Dict[str, Any]
    links: List[str]
    tags: List[str]
    entities: List[str]
    cost_usdc: str

@router.post("/api/v1/extract-obsidian", response_model=ObsidianExtractResponse)
async def extract_obsidian(request: ObsidianExtractRequest) -> ObsidianExtractResponse:
    """
    Extract structured data from Obsidian note.
    
    Price: 0.01 USDC per note
    """
    # Construct file path
    note_file = Path(request.vault_root) / request.note_path
    
    # Check if file exists
    if not note_file.exists():
        raise HTTPException(status_code=404, detail=f"Note not found: {request.note_path}")
    
    # Read note content
    try:
        content = note_file.read_text(encoding='utf-8')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read note: {str(e)}")
    
    # Extract links (markdown links and wiki links)
    links = []
    if request.extract_links:
        import re
        # Wiki links: [[link]]
        wiki_links = re.findall(r'\[\[(.*?)\]\]', content)
        # Markdown links: [text](url)
        md_links = re.findall(r'\[(.*?)\]\((.*?)\)', content)
        links = list(set(wiki_links + [m[1] for m in md_links]))
    
    # Extract tags
    tags = []
    if request.extract_tags:
        import re
        tags = list(set(re.findall(r'#(\w+)', content)))
    
    # Extract simple entities (placeholder - can enhance with NLP)
    entities = []
    # Look for capitalized words (simple entity detection)
    import re
    potential_entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
    entities = list(set(potential_entities))[:20]  # Limit to 20
    
    # Metadata
    metadata = {
        "file_size": len(content),
        "word_count": len(content.split()),
        "line_count": len(content.splitlines()),
        "vault_root": request.vault_root,
    }
    
    return ObsidianExtractResponse(
        content=content[:1000] + "..." if len(content) > 1000 else content,
        metadata=metadata,
        links=links,
        tags=tags,
        entities=entities,
        cost_usdc="0.01",
    )
