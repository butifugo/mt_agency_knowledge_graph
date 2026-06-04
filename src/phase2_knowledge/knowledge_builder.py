"""
Knowledge Graph Builder
Builds document knowledge graphs from markdown files
"""

import re
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from urllib.parse import urlparse
from collections import defaultdict
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.shared.schemas import KnowledgeNode, KnowledgeEdge, Document, NodeType, EdgeType
from src.shared.utils import normalize_url, get_mime_type


class KnowledgeBuilder:
    """Builds knowledge graph from crawled markdown documents"""
    
    def __init__(self, knowledge_dir: str = "knowledge", output_dir: str = "data/graphs/knowledge"):
        """
        Initialize knowledge builder
        
        Args:
            knowledge_dir: Directory containing crawled markdown files
            output_dir: Directory for knowledge graph output
        """
        self.knowledge_dir = Path(knowledge_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Graph components
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: List[KnowledgeEdge] = []
        
        # URL and file mappings
        self.url_to_id: Dict[str, str] = {}
        self.file_to_id: Dict[str, str] = {}
        
        # Statistics
        self.stats = {
            'total_nodes': 0,
            'total_edges': 0,
            'agencies': set(),
            'document_types': defaultdict(int)
        }
    
    def _extract_metadata(self, md_file: Path) -> Dict[str, str]:
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
    
    def _extract_content(self, md_file: Path) -> str:
        """Extract main content from markdown (excluding frontmatter)"""
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                return parts[2].strip()
        
        return content
    
    def _extract_links(self, content: str) -> List[Tuple[str, str, str]]:
        """
        Extract all links from markdown content
        Returns: List of (link_text, url, context)
        """
        links = []
        
        # Pattern: [text](url)
        link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        
        for match in re.finditer(link_pattern, content):
            link_text = match.group(1)
            url = match.group(2)
            
            # Get surrounding context (50 chars before and after)
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 50)
            context = content[start:end].replace('\n', ' ')
            
            links.append((link_text, url, context))
        
        return links
    
    def _extract_keywords(self, content: str, title: str) -> List[str]:
        """Extract basic keywords from content and title"""
        text = (title + ' ' + content).lower()
        
        # Remove markdown syntax
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Links
        text = re.sub(r'[#*`_\-]', ' ', text)  # Markdown characters
        
        # Split into words
        words = re.findall(r'\b[a-z]{4,}\b', text)  # Words 4+ chars
        
        # Count frequencies
        word_freq = defaultdict(int)
        for word in words:
            word_freq[word] += 1
        
        # Exclude common words
        common_words = {
            'that', 'with', 'from', 'this', 'have', 'will', 'your',
            'more', 'about', 'other', 'which', 'their', 'there', 'than',
            'been', 'were', 'when', 'where', 'what', 'these', 'those',
            'would', 'could', 'should', 'also', 'some', 'only', 'such'
        }
        
        keywords = [
            word for word, count in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            if word not in common_words and count >= 2
        ][:20]
        
        return keywords
    
    def _generate_node_id(self, file_path: Path) -> str:
        """Generate unique node ID from file path"""
        relative_path = file_path.relative_to(self.knowledge_dir)
        return str(relative_path.with_suffix(''))
    
    def _resolve_link_to_node(self, url: str, source_file: Path) -> Optional[str]:
        """Try to resolve a URL to a node ID in the graph"""
        # Try absolute URL lookup
        if url.startswith('http'):
            normalized = normalize_url(url)
            if normalized in self.url_to_id:
                return self.url_to_id[normalized]
        
        # Try relative path resolution
        if url.startswith('..') or url.startswith('./'):
            filename = Path(url).name
            for md_file in self.knowledge_dir.rglob('*.md'):
                if md_file.name == filename or md_file.stem in url:
                    return self._generate_node_id(md_file)
        
        # Try filename-based matching
        if '/' in url or '\\' in url:
            filename = Path(url).stem
            if filename in self.file_to_id:
                return self.file_to_id[filename]
        
        return None
    
    def build_knowledge_graph(self, agency: str, verbose: bool = True) -> Dict:
        """
        Build knowledge graph for a specific agency
        
        Args:
            agency: Agency folder name
            verbose: Print progress
            
        Returns:
            Dictionary with knowledge graph data
        """
        agency_dir = self.knowledge_dir / agency
        
        if not agency_dir.exists():
            if verbose:
                print(f"✗ Agency directory not found: {agency_dir}")
            return {}
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"Building Knowledge Graph: {agency}")
            print(f"{'='*80}\n")
        
        # Reset for this agency
        self.nodes = {}
        self.edges = []
        self.url_to_id = {}
        self.file_to_id = {}
        self.stats = {
            'total_nodes': 0,
            'total_edges': 0,
            'agencies': {agency},
            'document_types': defaultdict(int)
        }
        
        # Step 1: Create nodes from all markdown files
        md_files = list(agency_dir.glob('*.md'))
        
        if verbose:
            print(f"Found {len(md_files)} markdown files")
            print("Building nodes...")
        
        for md_file in md_files:
            metadata = self._extract_metadata(md_file)
            content = self._extract_content(md_file)
            
            if not metadata.get('source'):
                continue
            
            node_id = self._generate_node_id(md_file)
            source_url = metadata['source']
            title = metadata.get('title', 'Untitled')
            
            # Extract keywords
            keywords = self._extract_keywords(content, title)
            
            # Determine document type
            file_name = md_file.name.lower()
            if file_name.startswith('pdf_'):
                node_type = NodeType.PDF_DOCUMENT
            elif file_name.startswith('_docs_'):
                node_type = NodeType.DOCX_DOCUMENT
            else:
                node_type = NodeType.HTML_PAGE
            
            # Create document
            document = Document(
                id=node_id,
                url=source_url,
                title=title,
                content=content,
                mime_type=get_mime_type(source_url),
                file_path=str(md_file.relative_to(self.knowledge_dir)),
                agency=agency,
                crawled_date=datetime.now(),
                word_count=len(content.split()),
                metadata=metadata
            )
            
            # Create node
            node = KnowledgeNode(
                id=node_id,
                document=document,
                keywords=keywords,
                node_type=node_type
            )
            
            self.nodes[node_id] = node
            self.url_to_id[source_url] = node_id
            self.file_to_id[md_file.stem] = node_id
            
            self.stats['document_types'][node_type.value] += 1
        
        self.stats['total_nodes'] = len(self.nodes)
        
        if verbose:
            print(f"  Created {self.stats['total_nodes']} nodes")
            for doc_type, count in self.stats['document_types'].items():
                print(f"    {doc_type}: {count}")
        
        # Step 2: Extract links and create edges
        if verbose:
            print("\nBuilding edges...")
        
        for md_file in md_files:
            node_id = self._generate_node_id(md_file)
            
            if node_id not in self.nodes:
                continue
            
            content = self._extract_content(md_file)
            links = self._extract_links(content)
            
            for link_text, url, context in links:
                target_id = self._resolve_link_to_node(url, md_file)
                
                if not target_id or target_id not in self.nodes:
                    continue
                
                # Create edge
                edge = KnowledgeEdge(
                    source=node_id,
                    target=target_id,
                    edge_type=EdgeType.HYPERLINK,
                    metadata={
                        'link_text': link_text,
                        'context': context[:200]
                    }
                )
                
                self.edges.append(edge)
                self.stats['total_edges'] += 1
        
        if verbose:
            print(f"  Created {self.stats['total_edges']} edges")
        
        # Step 3: Export knowledge graph
        output_file = self.output_dir / f"{agency}_knowledge.json"
        
        knowledge_data = {
            'agency': agency,
            'created': datetime.now().isoformat(),
            'statistics': {
                'total_nodes': self.stats['total_nodes'],
                'total_edges': self.stats['total_edges'],
                'document_types': dict(self.stats['document_types'])
            },
            'nodes': {
                node_id: {
                    'id': node.id,
                    'title': node.document.title,
                    'url': node.document.url,
                    'type': node.node_type.value,
                    'agency': node.document.agency,
                    'keywords': node.keywords,
                    'file_path': node.document.file_path,
                    'word_count': node.document.word_count,
                    'metadata': node.document.metadata
                }
                for node_id, node in self.nodes.items()
            },
            'edges': [
                {
                    'source': edge.source,
                    'target': edge.target,
                    'type': edge.edge_type.value,
                    'link_text': edge.metadata.get('link_text', ''),
                    'context': edge.metadata.get('context', ''),
                    'weight': edge.weight
                }
                for edge in self.edges
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(knowledge_data, f, indent=2, ensure_ascii=False)
        
        if verbose:
            print(f"\n✓ Knowledge graph saved: {output_file}")
            print(f"{'='*80}\n")
        
        return knowledge_data
    
    def build_all_agencies(self, verbose: bool = True) -> Dict[str, Dict]:
        """
        Build knowledge graphs for all agencies
        
        Args:
            verbose: Print progress
            
        Returns:
            Dictionary mapping agency names to knowledge data
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
            
            knowledge_data = self.build_knowledge_graph(agency, verbose=False)
            
            if knowledge_data:
                results[agency] = knowledge_data
                
                if verbose:
                    print(f"  ✓ Nodes: {knowledge_data.get('statistics', {}).get('total_nodes', 0)}, "
                          f"Edges: {knowledge_data.get('statistics', {}).get('total_edges', 0)}")
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"✓ Built knowledge graphs for {len(results)} agencies")
            print(f"{'='*80}\n")
        
        return results
