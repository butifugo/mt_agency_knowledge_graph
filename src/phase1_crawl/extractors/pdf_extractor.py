"""
PDF Extractor
Extracts text content from PDF documents
"""

import io
from pathlib import Path
from PyPDF2 import PdfReader
from typing import Optional


class PdfExtractor:
    """Extract text from PDF documents"""
    
    @staticmethod
    def extract(pdf_bytes: bytes, url: str, timestamp: str) -> Optional[str]:
        """
        Extract text from PDF and convert to markdown
        
        Args:
            pdf_bytes: PDF file bytes
            url: Source URL
            timestamp: Crawl timestamp
            
        Returns:
            Markdown content or None if extraction fails
        """
        try:
            # Read PDF from bytes
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PdfReader(pdf_file)
            
            # Extract text from all pages
            text_content = []
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                if text.strip():
                    text_content.append(f"## Page {page_num}\n\n{text}")
            
            # Get PDF metadata
            metadata = pdf_reader.metadata
            title = metadata.title if metadata and metadata.title else Path(url).stem
            
            # Create markdown header
            header = f"""---
source: {url}
title: {title}
type: pdf
pages: {len(pdf_reader.pages)}
crawled: {timestamp}
---

# {title}

"""
            
            return header + "\n\n".join(text_content)
            
        except Exception as e:
            print(f"  ✗ Error extracting PDF: {str(e)}")
            return None
