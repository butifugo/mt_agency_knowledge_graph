"""
Navigation Network Builder
Builds webpage-centric navigation graph with MIME type hierarchy
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.shared.schemas import NavigationNode, NavigationEdge
from src.shared.utils import get_mime_type, normalize_url


class NavigationBuilder:
    """
    Builds navigation network from crawled markdown files
    Creates webpage-centric hierarchy with MIME types
    """
    
    def __init__(self, knowledge_dir: str = "knowledge", output_dir: str = "data/graphs/navigation"):
        """
        Initialize navigation builder
        
        Args:
            knowledge_dir: Directory containing crawled markdown files
            output_dir: Directory for navigation graph output
        """
        self.knowledge_dir = Path(knowledge_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Navigation graph components
        self.nodes: Dict[str, NavigationNode] = {}
        self.edges: List[NavigationEdge] = []
        
        # URL to node ID mapping
        self.url_to_id: Dict[str, str] = {}
        
        # Statistics
        self.stats = {
            'html_pages': 0,
            'pdf_documents': 0,
            'docx_documents': 0,
            'total_edges': 0
        }
    
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
                        metadata[key.strip()] = value.strip()
        
        return metadata
    
    def _extract_links_from_markdown(self, md_file: Path) -> List[Tuple[str, str]]:
        """Extract all links from markdown content"""
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2]
        
        import re
        links = []
        # Pattern: [text](url)
        link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        
        for match in re.finditer(link_pattern, content):
            link_text = match.group(1)
            url = match.group(2)
            links.append((link_text, url))
        
        return links
    
    def _generate_node_id(self, url: str) -> str:
        """Generate unique node ID from URL"""
        return hashlib.md5(url.encode()).hexdigest()[:12]
    
    def _classify_document_type(self, file_path: Path, metadata: Dict) -> str:
        """Classify document type from file path and metadata"""
        file_name = file_path.name.lower()
        
        # Check metadata first
        if 'type' in metadata:
            doc_type = metadata['type'].lower()
            if doc_type == 'pdf':
                return 'pdf_document'
            elif doc_type in ['docx', 'doc']:
                return 'docx_document'
            elif doc_type == 'html':
                return 'html_page'
        
        # Check filename
        if file_name.startswith('pdf_'):
            return 'pdf_document'
        elif file_name.startswith('_docs_'):
            return 'docx_document'
        else:
            return 'html_page'
    
    def build_navigation_graph(self, agency: str, verbose: bool = True) -> Dict:
        """
        Build navigation graph for a specific agency
        
        Args:
            agency: Agency folder name
            verbose: Print progress
            
        Returns:
            Dictionary with navigation graph data
        """
        agency_dir = self.knowledge_dir / agency
        
        if not agency_dir.exists():
            if verbose:
                print(f"✗ Agency directory not found: {agency_dir}")
            return {}
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"Building Navigation Graph: {agency}")
            print(f"{'='*80}\n")
        
        # Reset for this agency
        self.nodes = {}
        self.edges = []
        self.url_to_id = {}
        self.stats = {
            'html_pages': 0,
            'pdf_documents': 0,
            'docx_documents': 0,
            'total_edges': 0
        }
        
        # Step 1: Scan all markdown files and create nodes
        md_files = list(agency_dir.glob('*.md'))
        
        if verbose:
            print(f"Found {len(md_files)} markdown files")
            print("Building nodes...")
        
        for md_file in md_files:
            metadata = self._extract_metadata_from_markdown(md_file)
            
            if 'source' not in metadata:
                continue
            
            source_url = metadata['source']
            node_id = self._generate_node_id(source_url)
            
            # Determine document type
            doc_type = self._classify_document_type(md_file, metadata)
            mime_type = get_mime_type(source_url)
            
            # Create node
            node = NavigationNode(
                id=node_id,
                url=source_url,
                title=metadata.get('title', 'Untitled'),
                node_type=doc_type,
                mime_type=mime_type,
                level=0,  # Will be calculated later
                file_path=str(md_file.relative_to(self.knowledge_dir)),
                metadata=metadata
            )
            
            self.nodes[node_id] = node
            self.url_to_id[source_url] = node_id
            
            # Update stats
            if doc_type == 'html_page':
                self.stats['html_pages'] += 1
            elif doc_type == 'pdf_document':
                self.stats['pdf_documents'] += 1
            elif doc_type == 'docx_document':
                self.stats['docx_documents'] += 1
        
        if verbose:
            print(f"  Created {len(self.nodes)} nodes")
            print(f"  HTML pages: {self.stats['html_pages']}")
            print(f"  PDF documents: {self.stats['pdf_documents']}")
            print(f"  DOCX documents: {self.stats['docx_documents']}")
        
        # Step 2: Extract links and create edges
        if verbose:
            print("\nBuilding edges...")
        
        for md_file in md_files:
            metadata = self._extract_metadata_from_markdown(md_file)
            
            if 'source' not in metadata:
                continue
            
            source_url = metadata['source']
            source_id = self.url_to_id.get(source_url)
            
            if not source_id:
                continue
            
            # Extract links from markdown
            links = self._extract_links_from_markdown(md_file)
            
            for link_text, target_url in links:
                # Try to find target node
                # Normalize URL for matching
                normalized_target = normalize_url(target_url) if target_url.startswith('http') else target_url
                
                target_id = None
                for url, nid in self.url_to_id.items():
                    if url == target_url or normalize_url(url) == normalized_target:
                        target_id = nid
                        break
                
                if not target_id:
                    continue
                
                # Determine edge type
                target_node = self.nodes[target_id]
                if target_node.node_type in ['pdf_document', 'docx_document']:
                    edge_type = 'document_link'
                else:
                    edge_type = 'hyperlink'
                
                # Create edge
                edge = NavigationEdge(
                    source=source_id,
                    target=target_id,
                    link_text=link_text,
                    edge_type=edge_type
                )
                
                self.edges.append(edge)
                self.stats['total_edges'] += 1
                
                # Update parent-child relationships
                if target_node.parent is None:
                    target_node.parent = source_id
                
                source_node = self.nodes[source_id]
                if target_id not in source_node.children:
                    source_node.children.append(target_id)
        
        if verbose:
            print(f"  Created {self.stats['total_edges']} edges")
        
        # Step 3: Calculate hierarchy levels
        if verbose:
            print("\nCalculating hierarchy levels...")
        
        self._calculate_hierarchy_levels(agency)
        
        # Step 4: Export navigation graph
        output_file = self.output_dir / f"{agency}_navigation.json"
        
        nav_data = {
            'agency': agency,
            'created': datetime.now().isoformat(),
            'statistics': self.stats,
            'nodes': {
                node_id: {
                    'id': node.id,
                    'url': node.url,
                    'title': node.title,
                    'type': node.node_type,
                    'mime_type': node.mime_type,
                    'level': node.level,
                    'parent': node.parent,
                    'children': node.children,
                    'file_path': node.file_path
                }
                for node_id, node in self.nodes.items()
            },
            'edges': [
                {
                    'source': edge.source,
                    'target': edge.target,
                    'link_text': edge.link_text,
                    'type': edge.edge_type
                }
                for edge in self.edges
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(nav_data, f, indent=2, ensure_ascii=False)
        
        if verbose:
            print(f"\n✓ Navigation graph saved: {output_file}")
            print(f"{'='*80}\n")
        
        return nav_data
    
    def _calculate_hierarchy_levels(self, agency: str):
        """Calculate hierarchy depth levels for all nodes"""
        # Find root node (usually index page)
        root_id = None
        for node_id, node in self.nodes.items():
            if node.parent is None and node.node_type == 'html_page':
                if 'index' in node.url.lower() or node.url.endswith('/'):
                    root_id = node_id
                    break
        
        # If no index found, use first HTML page without parent
        if not root_id:
            for node_id, node in self.nodes.items():
                if node.parent is None and node.node_type == 'html_page':
                    root_id = node_id
                    break
        
        if not root_id:
            return
        
        # BFS to calculate levels
        from collections import deque
        
        queue = deque([(root_id, 0)])
        visited = set()
        
        while queue:
            node_id, level = queue.popleft()
            
            if node_id in visited:
                continue
            
            visited.add(node_id)
            
            node = self.nodes[node_id]
            node.level = level
            
            # Add children to queue
            for child_id in node.children:
                if child_id not in visited:
                    queue.append((child_id, level + 1))
    
    def build_all_agencies(self, verbose: bool = True) -> Dict[str, Dict]:
        """
        Build navigation graphs for all agencies
        
        Args:
            verbose: Print progress
            
        Returns:
            Dictionary mapping agency names to navigation data
        """
        results = {}
        
        # Find all agency directories
        agency_dirs = [d for d in self.knowledge_dir.iterdir() if d.is_dir()]
        
        if verbose:
            print(f"\nFound {len(agency_dirs)} agencies to process\n")
        
        for i, agency_dir in enumerate(agency_dirs, 1):
            agency = agency_dir.name
            
            if verbose:
                print(f"[{i}/{len(agency_dirs)}] Processing: {agency}")
            
            nav_data = self.build_navigation_graph(agency, verbose=False)
            
            if nav_data:
                results[agency] = nav_data
                
                if verbose:
                    print(f"  ✓ Nodes: {len(nav_data.get('nodes', {}))}, "
                          f"Edges: {nav_data.get('statistics', {}).get('total_edges', 0)}")
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"✓ Built navigation graphs for {len(results)} agencies")
            print(f"{'='*80}\n")
        
        return results
