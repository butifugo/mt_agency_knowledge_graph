"""
HTML Navigation Extractor
Extracts pure HTML navigation structure from crawled markdown files
Focuses on webpage-to-webpage links, not knowledge relationships
"""

import json
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from datetime import datetime
from urllib.parse import urlparse, urljoin


class HTMLNavigationExtractor:
    """
    Extracts HTML navigation links from crawled markdown files.
    Creates a simple navigational graph with MIME-type hierarchy.
    """
    
    def __init__(self, knowledge_dir: str = "knowledge", output_dir: str = "data/graphs/navigation"):
        """
        Initialize extractor
        
        Args:
            knowledge_dir: Directory containing crawled markdown files
            output_dir: Directory for navigation graph output
        """
        self.knowledge_dir = Path(knowledge_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Graph components
        self.nodes: Dict[str, Dict] = {}
        self.edges: List[Dict] = []
        
        # URL tracking
        self.url_to_id: Dict[str, str] = {}
        self.base_domain = None
        
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication"""
        # Remove trailing slash
        url = url.rstrip('/')
        # Remove fragment
        if '#' in url:
            url = url.split('#')[0]
        # Remove common tracking parameters
        if '?' in url:
            base_url, query = url.split('?', 1)
            # Keep query if it's not just tracking params
            # For now, keep all query params but normalize
            url = base_url
        return url
    
    def _generate_node_id(self, url: str) -> str:
        """Generate unique node ID from URL"""
        normalized = self._normalize_url(url)
        return hashlib.md5(normalized.encode()).hexdigest()[:12]
    
    def _get_mime_type_from_url(self, url: str) -> str:
        """Determine MIME type from URL"""
        url_lower = url.lower()
        
        if url_lower.endswith('.pdf'):
            return 'application/pdf'
        elif url_lower.endswith(('.doc', '.docx')):
            return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif url_lower.endswith(('.xls', '.xlsx')):
            return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif url_lower.endswith('.txt'):
            return 'text/plain'
        else:
            # Assume HTML for web pages
            return 'text/html'
    
    def _get_node_type_from_mime(self, mime_type: str) -> str:
        """Map MIME type to node type"""
        if mime_type == 'text/html':
            return 'html_page'
        elif mime_type == 'application/pdf':
            return 'pdf_document'
        elif 'word' in mime_type or mime_type == 'application/msword':
            return 'docx_document'
        elif 'excel' in mime_type or 'spreadsheet' in mime_type:
            return 'excel_document'
        else:
            return 'other_document'
    
    def _extract_metadata_from_markdown(self, md_file: Path) -> Dict[str, str]:
        """Extract YAML frontmatter from markdown file"""
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        metadata = {}
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = parts[1]
                for line in frontmatter.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip().strip('"\'')
        
        return metadata
    
    def _extract_links_from_markdown(self, md_file: Path, source_url: str) -> List[Tuple[str, str]]:
        """
        Extract all links from markdown content
        
        Returns:
            List of (link_text, target_url) tuples
        """
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2]
        
        links = []
        seen_urls = set()
        url_to_text = {}  # Map URL to best link text found
        
        # First pass: Extract all [text](url) patterns including nested ones
        # Pattern captures markdown links with text
        link_pattern = r'\[([^\]]*)\]\(([^\)]+)\)'
        
        for match in re.finditer(link_pattern, content):
            raw_text = match.group(1).strip()
            url = match.group(2).strip()
            
            # Remove any title attribute first (e.g., "url title" -> url)
            if ' "' in url:
                url = url.split(' "')[0].strip()
            
            # Skip anchors, images, and empty links
            if url.startswith('#') or not url or url.startswith('_images/'):
                continue
            
            # Resolve relative URLs using the full source URL as base
            if not url.startswith(('http://', 'https://')):
                url = urljoin(source_url, url)
            
            # Normalize URL for deduplication
            normalized_url = self._normalize_url(url)
            
            # Determine link text quality
            # Skip if it's an image reference (![ ])
            if raw_text.startswith('!'):
                # This is an image, but might be nested in a link
                # Check if we already have this URL with better text
                if normalized_url not in url_to_text:
                    # Use URL-based title as placeholder
                    link_text = self._extract_title_from_url(normalized_url)
                    url_to_text[normalized_url] = link_text
                continue
            
            # Clean the link text
            link_text = raw_text
            
            # If text contains nested markdown (like [![...](...)]), extract cleaner version
            if '![' in link_text or '[' in link_text:
                # Extract from nested structure or use URL
                link_text = self._extract_title_from_url(normalized_url)
            
            # Use this text if it's better than what we have (or first time seeing this URL)
            if normalized_url not in url_to_text or len(link_text) > len(url_to_text[normalized_url]):
                if link_text and not link_text.startswith('?'):
                    url_to_text[normalized_url] = link_text
        
        # Convert to list of tuples
        for url, text in url_to_text.items():
            links.append((text, url))
        
        return links
    
    def _extract_title_from_url(self, url: str) -> str:
        """
        Extract a reasonable title from a URL
        
        Args:
            url: URL to extract title from
            
        Returns:
            Extracted title
        """
        parsed = urlparse(url)
        path = parsed.path.rstrip('/')
        
        if path:
            # Get the last segment of the path
            segments = path.split('/')
            last_segment = segments[-1] if segments else ''
            
            # Remove file extension for cleaner title
            if '.' in last_segment:
                name = last_segment.rsplit('.', 1)[0]
            else:
                name = last_segment
            
            # Clean up: replace hyphens/underscores with spaces
            name = name.replace('-', ' ').replace('_', ' ')
            return name if name else parsed.netloc
        
        return parsed.netloc
    
    def _add_node(self, url: str, title: str, mime_type: str, file_path: Optional[str] = None) -> str:
        """
        Add node to graph if not already present
        
        Returns:
            Node ID
        """
        # Normalize URL for deduplication
        normalized_url = self._normalize_url(url)
        
        # Check if this normalized URL already exists
        if normalized_url in self.url_to_id:
            return self.url_to_id[normalized_url]
        
        node_id = self._generate_node_id(url)
        node_type = self._get_node_type_from_mime(mime_type)
        
        # Determine if this is the root domain
        is_root = False
        if self.base_domain and normalized_url == self.base_domain.rstrip('/'):
            is_root = True
        
        self.nodes[node_id] = {
            'id': node_id,
            'url': normalized_url,  # Store normalized URL
            'title': title,
            'mime_type': mime_type,
            'type': node_type,
            'is_root': is_root,
            'file_path': file_path
        }
        
        self.url_to_id[normalized_url] = node_id
        return node_id
    
    def _add_edge(self, source_id: str, target_id: str, link_text: str):
        """Add edge to graph"""
        # Check if edge already exists
        for edge in self.edges:
            if edge['source'] == source_id and edge['target'] == target_id:
                return
        
        self.edges.append({
            'source': source_id,
            'target': target_id,
            'link_text': link_text
        })
    
    def extract_navigation(self, agency: str, verbose: bool = True) -> Dict:
        """
        Extract HTML navigation structure for an agency
        
        Args:
            agency: Agency folder name
            verbose: Print progress
            
        Returns:
            Dictionary with navigation graph
        """
        agency_dir = self.knowledge_dir / agency
        
        if not agency_dir.exists():
            if verbose:
                print(f"✗ Agency directory not found: {agency_dir}")
            return {}
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"Extracting HTML Navigation: {agency}")
            print(f"{'='*80}\n")
        
        # Reset for this agency
        self.nodes = {}
        self.edges = []
        self.url_to_id = {}
        self.base_domain = None
        
        # Find all markdown files
        md_files = list(agency_dir.glob('*.md'))
        
        if verbose:
            print(f"Found {len(md_files)} markdown files")
        
        # First pass: Create all nodes
        for md_file in md_files:
            metadata = self._extract_metadata_from_markdown(md_file)
            
            source_url = metadata.get('source', '')
            title = metadata.get('title', md_file.stem)
            
            if not source_url:
                continue
            
            # Set base domain from first URL
            if not self.base_domain and source_url.startswith('http'):
                parsed = urlparse(source_url)
                self.base_domain = f"{parsed.scheme}://{parsed.netloc}"
            
            # Determine MIME type
            mime_type = self._get_mime_type_from_url(source_url)
            
            # Override with metadata if available
            if 'type' in metadata:
                if metadata['type'] == 'pdf':
                    mime_type = 'application/pdf'
                elif metadata['type'] == 'html':
                    mime_type = 'text/html'
            
            # Add node
            self._add_node(
                url=source_url,
                title=title,
                mime_type=mime_type,
                file_path=str(md_file.relative_to(self.knowledge_dir))
            )
        
        # Second pass: Create edges
        for md_file in md_files:
            metadata = self._extract_metadata_from_markdown(md_file)
            source_url = metadata.get('source', '')
            
            if not source_url:
                continue
            
            # Normalize source URL
            source_url_normalized = self._normalize_url(source_url)
            
            if source_url_normalized not in self.url_to_id:
                continue
            
            source_id = self.url_to_id[source_url_normalized]
            
            # Extract links
            links = self._extract_links_from_markdown(md_file, source_url)
            
            for link_text, target_url in links:
                # Add target node if not exists
                target_mime = self._get_mime_type_from_url(target_url)
                # Ensure we have a reasonable title (fallback for edge cases)
                if not link_text or link_text.startswith('?') or len(link_text) < 2:
                    link_text = self._extract_title_from_url(target_url)
                
                target_id = self._add_node(
                    url=target_url,
                    title=link_text,
                    mime_type=target_mime
                )
                
                # Add edge
                self._add_edge(source_id, target_id, link_text)
        
        # Calculate statistics
        stats = {
            'total_nodes': len(self.nodes),
            'html_pages': sum(1 for n in self.nodes.values() if n['type'] == 'html_page'),
            'pdf_documents': sum(1 for n in self.nodes.values() if n['type'] == 'pdf_document'),
            'docx_documents': sum(1 for n in self.nodes.values() if n['type'] == 'docx_document'),
            'other_documents': sum(1 for n in self.nodes.values() if n['type'] not in ['html_page', 'pdf_document', 'docx_document']),
            'total_edges': len(self.edges)
        }
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"Navigation Extraction Complete")
            print(f"{'='*80}")
            print(f"  Total Nodes: {stats['total_nodes']}")
            print(f"  - HTML Pages: {stats['html_pages']}")
            print(f"  - PDF Documents: {stats['pdf_documents']}")
            print(f"  - DOCX Documents: {stats['docx_documents']}")
            print(f"  - Other Documents: {stats['other_documents']}")
            print(f"  Total Edges: {stats['total_edges']}")
            print(f"{'='*80}\n")
        
        # Build result
        result = {
            'agency': agency,
            'created': datetime.now().isoformat(),
            'base_domain': self.base_domain,
            'statistics': stats,
            'nodes': self.nodes,
            'edges': self.edges
        }
        
        # Save to file
        output_file = self.output_dir / f"{agency}_html_navigation.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        if verbose:
            print(f"✓ Saved to: {output_file}\n")
        
        return result


if __name__ == '__main__':
    # Test extraction
    extractor = HTMLNavigationExtractor()
    result = extractor.extract_navigation('agriculture', verbose=True)
