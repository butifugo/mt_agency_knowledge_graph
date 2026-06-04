"""
HTML Extractor
Converts HTML pages to clean markdown format
"""

import re
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from typing import Tuple


class HtmlExtractor:
    """Extract and convert HTML content to markdown"""
    
    @staticmethod
    def clean_content(soup: BeautifulSoup) -> BeautifulSoup:
        """Remove navigation, scripts, and other non-content elements"""
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()
        
        # Remove common navigation/sidebar classes
        for element in soup.find_all(class_=re.compile(r'nav|sidebar|footer|header|menu', re.I)):
            element.decompose()
        
        # Remove common navigation IDs
        for element in soup.find_all(id=re.compile(r'nav|sidebar|footer|header|menu', re.I)):
            element.decompose()
            
        return soup
    
    @staticmethod
    def extract(html: str, url: str, timestamp: str) -> Tuple[str, str]:
        """
        Convert HTML to markdown with metadata
        
        Args:
            html: HTML content
            url: Source URL
            timestamp: Crawl timestamp
            
        Returns:
            Tuple of (markdown_content, page_title)
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Clean the content
        soup = HtmlExtractor.clean_content(soup)
        
        # Get the main content area if it exists
        main_content = (soup.find('main') or 
                       soup.find('article') or 
                       soup.find(id='content') or 
                       soup.find(class_=re.compile(r'content|main', re.I)) or 
                       soup)
        
        # Get page title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "Untitled"
        
        # Convert to markdown
        markdown_content = md(str(main_content), heading_style="ATX", bullets="-")
        
        # Create header with metadata
        header = f"""---
source: {url}
title: {title_text}
crawled: {timestamp}
type: html
---

# {title_text}

"""
        
        # Clean up markdown (remove excessive newlines)
        markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
        
        return header + markdown_content, title_text
