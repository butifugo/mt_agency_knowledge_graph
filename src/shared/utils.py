"""
Shared Utilities
Common functions used across multiple phases
"""

import hashlib
import re
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional


def normalize_url(url: str) -> str:
    """
    Normalize URL for comparison
    
    Args:
        url: URL to normalize
        
    Returns:
        Normalized URL
    """
    parsed = urlparse(url)
    # Remove fragments and trailing slashes
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
    if parsed.query:
        normalized += f"?{parsed.query}"
    return normalized


def get_file_hash(content: str) -> str:
    """
    Get MD5 hash of content
    
    Args:
        content: Content to hash
        
    Returns:
        MD5 hash as hex string
    """
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def clean_filename(filename: str) -> str:
    """
    Clean filename for safe filesystem use
    
    Args:
        filename: Original filename
        
    Returns:
        Cleaned filename
    """
    # Remove or replace unsafe characters
    filename = re.sub(r'[^\w\-_.]', '_', filename)
    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    return filename


def extract_agency_from_path(file_path: str) -> Optional[str]:
    """
    Extract agency name from file path
    
    Args:
        file_path: Path to file
        
    Returns:
        Agency name or None
    """
    path = Path(file_path)
    parts = path.parts
    
    # Look for knowledge directory in path
    if 'knowledge' in parts:
        idx = parts.index('knowledge')
        if idx + 1 < len(parts):
            return parts[idx + 1]
    
    return None


def get_mime_type(file_path: str) -> str:
    """
    Determine MIME type from file extension
    
    Args:
        file_path: Path to file
        
    Returns:
        MIME type string
    """
    ext = Path(file_path).suffix.lower()
    
    mime_types = {
        '.html': 'text/html',
        '.htm': 'text/html',
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.doc': 'application/msword'
    }
    
    return mime_types.get(ext, 'application/octet-stream')


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    size = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"
