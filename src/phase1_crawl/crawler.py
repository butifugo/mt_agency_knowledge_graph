"""
Web Crawler
Main crawler engine for extracting website content
"""

import time
import re
import requests
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import Set, Tuple, Optional
from bs4 import BeautifulSoup

from .extractors import HtmlExtractor, PdfExtractor, DocxExtractor
from ..shared.utils import normalize_url, clean_filename


class WebCrawler:
    """
    Web crawler for Montana state agency websites
    Extracts HTML, PDF, and DOCX content
    """
    
    def __init__(
        self,
        base_url: str,
        output_dir: str,
        agency_name: str = "Montana State Agency",
        rate_limit: float = 1.0,
        timeout: int = 30,
        user_agent: str = "Mozilla/5.0 (Montana Knowledge Crawler)",
        start_url: Optional[str] = None,
        max_pages: Optional[int] = None
    ):
        """
        Initialize crawler

        Args:
            base_url: Base URL to start crawling
            output_dir: Output directory for markdown files
            agency_name: Agency name
            rate_limit: Delay between requests (seconds)
            timeout: Request timeout (seconds)
            user_agent: User agent string
            start_url: Optional subtree URL to scope the crawl to. When given,
                the crawl seeds from this URL and only follows HTML links under
                it (e.g. https://dphhs.mt.gov/aging crawls just that section).
                Used to crawl a large site one piece at a time.
            max_pages: Optional hard cap on the number of HTML pages to crawl.
                Acts as a safety brake so a large subtree can't run away.
        """
        # When a start_url is given it both seeds the frontier and defines the
        # subtree the crawl is confined to (see extract_links).
        self.base_url = (start_url or base_url).rstrip('/')
        self.max_pages = max_pages
        self.output_dir = Path(output_dir)
        self.agency_name = agency_name
        self.rate_limit = rate_limit
        self.timeout = timeout
        
        # Create session
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': user_agent})
        
        # Track visited URLs
        self.visited_urls: Set[str] = set()
        self.to_visit: Set[str] = {self.base_url}
        
        # Statistics
        self.stats = {
            'html_pages': 0,
            'pdf_documents': 0,
            'docx_documents': 0,
            'errors': 0
        }
        
        # Domain for validation (derived from the effective start URL)
        self.domain = urlparse(self.base_url).netloc

    def _reached_cap(self) -> bool:
        """True once the max_pages ceiling is hit (no cap → never)."""
        return self.max_pages is not None and self.stats['html_pages'] >= self.max_pages

    def is_valid_url(self, url: str) -> bool:
        """Check if URL belongs to the agency's domain"""
        parsed = urlparse(url)
        
        # Check domain
        if not (parsed.netloc == self.domain or parsed.netloc == ''):
            return False
        
        # Check file extension
        path_lower = parsed.path.lower()
        
        # Allow PDFs and DOCX
        if any(path_lower.endswith(ext) for ext in ['.pdf', '.docx', '.doc']):
            return True
        
        # Allow HTML pages
        if any(path_lower.endswith(ext) for ext in ['.html', '.htm']):
            return True
        
        # If no extension or ends with '/', assume it's an HTML page
        if '.' not in Path(parsed.path).name or path_lower.endswith('/'):
            return True
        
        return False
    
    def get_output_path(self, url: str, file_type: str = 'html') -> Path:
        """Convert URL to file path"""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        if not path:
            path = 'index'
        
        # Clean up path for filename
        path = path.replace('/', '_')
        path = clean_filename(path)
        
        # Add prefix for non-HTML files
        if file_type == 'pdf':
            path = f'pdf_{path}'
        elif file_type == 'docx':
            path = f'_docs_{path}'
        
        return self.output_dir / f"{path}.md"
    
    def extract_links(self, soup: BeautifulSoup, current_url: str) -> Tuple[Set[str], Set[str], Set[str]]:
        """
        Extract links from page
        
        Returns:
            Tuple of (html_links, pdf_links, docx_links)
        """
        html_links = set()
        pdf_links = set()
        docx_links = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if not isinstance(href, str):
                continue
            
            absolute_url = urljoin(current_url, href)
            
            if not self.is_valid_url(absolute_url):
                continue
            
            # Classify by type
            if absolute_url.lower().endswith('.pdf'):
                pdf_links.add(absolute_url)
            elif absolute_url.lower().endswith(('.docx', '.doc')):
                docx_links.add(absolute_url)
            else:
                normalized = normalize_url(absolute_url)
                if normalized.startswith(self.base_url):
                    html_links.add(normalized)
        
        return html_links, pdf_links, docx_links
    
    def process_html_page(self, url: str) -> Set[str]:
        """Process HTML page and extract links"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Extract and convert to markdown
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            markdown_content, title = HtmlExtractor.extract(response.text, url, timestamp)
            
            # Save to file
            output_path = self.get_output_path(url, 'html')
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"✓ HTML: {title[:60]}")
            self.stats['html_pages'] += 1
            
            # Extract links
            soup = BeautifulSoup(response.text, 'html.parser')
            html_links, pdf_links, docx_links = self.extract_links(soup, url)
            
            # Process PDFs and DOCX (these are fetches too, so they count
            # against max_pages — the cap is a ceiling on total URLs hit).
            for pdf_url in pdf_links:
                if self._reached_cap():
                    break
                if pdf_url not in self.visited_urls:
                    self.visited_urls.add(pdf_url)
                    self.process_pdf(pdf_url)

            for docx_url in docx_links:
                if self._reached_cap():
                    break
                if docx_url not in self.visited_urls:
                    self.visited_urls.add(docx_url)
                    self.process_docx(docx_url)

            return html_links
            
        except Exception as e:
            print(f"✗ Error: {url}: {str(e)[:50]}")
            self.stats['errors'] += 1
            return set()
    
    def process_pdf(self, url: str):
        """Process PDF document"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            markdown_content = PdfExtractor.extract(response.content, url, timestamp)
            
            if not markdown_content:
                return
            
            output_path = self.get_output_path(url, 'pdf')
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"✓ PDF: {Path(url).name[:60]}")
            self.stats['pdf_documents'] += 1
            
        except Exception as e:
            print(f"✗ PDF Error: {url}: {str(e)[:50]}")
            self.stats['errors'] += 1
    
    def process_docx(self, url: str):
        """Process DOCX document"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            markdown_content = DocxExtractor.extract(response.content, url, timestamp)
            
            if not markdown_content:
                return
            
            output_path = self.get_output_path(url, 'docx')
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"✓ DOCX: {Path(url).name[:60]}")
            self.stats['docx_documents'] += 1
            
        except Exception as e:
            print(f"✗ DOCX Error: {url}: {str(e)[:50]}")
            self.stats['errors'] += 1
    
    def crawl(self) -> dict:
        """
        Main crawl loop
        
        Returns:
            Statistics dictionary
        """
        print(f"\n{'='*80}")
        print(f"Starting crawl: {self.agency_name}")
        print(f"URL: {self.base_url}")
        print(f"Output: {self.output_dir.absolute()}")
        if self.max_pages is not None:
            print(f"Max pages: {self.max_pages}")
        print(f"{'='*80}\n")

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        while self.to_visit:
            # Safety brake: stop once we've crawled the requested page count
            if self.max_pages is not None and self.stats['html_pages'] >= self.max_pages:
                print(f"\nℹ Reached max pages ({self.max_pages}) — stopping. "
                      f"{len(self.to_visit)} URLs left in frontier.")
                break

            url = self.to_visit.pop()

            if url in self.visited_urls:
                continue
            
            self.visited_urls.add(url)
            
            # Crawl the page
            new_links = self.process_html_page(url)
            
            # Add new links to queue
            unvisited_links = new_links - self.visited_urls
            self.to_visit.update(unvisited_links)
            
            # Rate limiting
            time.sleep(self.rate_limit)
        
        # Print summary
        print(f"\n{'='*80}")
        print(f"✓ Crawl complete: {self.agency_name}")
        print(f"  HTML pages: {self.stats['html_pages']}")
        print(f"  PDF documents: {self.stats['pdf_documents']}")
        print(f"  DOCX documents: {self.stats['docx_documents']}")
        print(f"  Errors: {self.stats['errors']}")
        print(f"  Total files: {len(list(self.output_dir.glob('*.md')))}")
        print(f"{'='*80}\n")
        
        return {
            'agency': self.agency_name,
            'url': self.base_url,
            **self.stats,
            'total_files': len(list(self.output_dir.glob('*.md')))
        }
