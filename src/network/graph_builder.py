"""
Graph Builder - Phase 1
Builds the document knowledge graph from markdown files
Extracts links, metadata, and creates the network structure
"""

import re
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from urllib.parse import urlparse, urljoin
from collections import defaultdict
from datetime import datetime

from src.network.schema import (
    KnowledgeGraph, NodeMetadata, EdgeMetadata, ContentChunk,
    NodeType, EdgeType, create_node_from_markdown
)


class GraphBuilder:
    """Builds knowledge graph from markdown documents"""
    
    def __init__(self, knowledge_dir: str = "knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.graph = KnowledgeGraph()
        
        # Temporary mappings for link resolution
        self.url_to_node: Dict[str, str] = {}  # source_url -> node_id
        self.file_to_node: Dict[str, str] = {}  # filename -> node_id
        
    def extract_metadata(self, md_file: Path) -> Dict[str, str]:
        """Extract YAML frontmatter metadata from markdown file"""
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
    
    def extract_content(self, md_file: Path) -> str:
        """Extract main content from markdown (excluding frontmatter)"""
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                return parts[2].strip()
        
        return content
    
    def extract_links(self, content: str) -> List[Tuple[str, str, str]]:
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
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL for comparison"""
        # Remove fragments and trailing slashes
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized
    
    def resolve_link_to_node(self, url: str, source_file: Path) -> Optional[str]:
        """
        Try to resolve a URL to a node ID in the graph
        Handles both absolute URLs and relative paths
        """
        # Try absolute URL lookup
        normalized = self.normalize_url(url) if url.startswith('http') else url
        if normalized in self.url_to_node:
            return self.url_to_node[normalized]
        
        # Try relative path resolution
        if url.startswith('..') or url.startswith('./'):
            # Extract filename from relative path
            filename = Path(url).name
            # Try to find matching file
            for md_file in self.knowledge_dir.rglob('*.md'):
                if md_file.name == filename or md_file.stem in url:
                    relative_path = str(md_file.relative_to(self.knowledge_dir).with_suffix(''))
                    if relative_path in self.graph.nodes:
                        return relative_path
        
        # Try filename-based matching
        if '/' in url or '\\' in url:
            filename = Path(url).stem
            if filename in self.file_to_node:
                return self.file_to_node[filename]
        
        return None
    
    def extract_keywords(self, content: str, title: str) -> List[str]:
        """Extract basic keywords from content and title"""
        # Simple keyword extraction (can be enhanced with NLP)
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
        
        # Get top keywords (excluding common words)
        common_words = {
            'that', 'with', 'from', 'this', 'have', 'will', 'your',
            'more', 'about', 'other', 'which', 'their', 'there', 'than',
            'been', 'were', 'when', 'where', 'what', 'these', 'those'
        }
        
        keywords = [
            word for word, count in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            if word not in common_words and count >= 2
        ][:20]
        
        return keywords
    
    def extract_topics(self, content: str, agency: str) -> List[str]:
        """Extract topic tags from content"""
        topics = [agency]  # Agency is always a topic
        
        # Look for common HR/government topics
        topic_patterns = {
            'employment': r'\b(employment|job|hire|hiring|career|position)\b',
            'benefits': r'\b(benefit|insurance|retirement|pension|health)\b',
            'policy': r'\b(policy|policies|rule|regulation|guideline)\b',
            'training': r'\b(training|development|education|learning)\b',
            'payroll': r'\b(payroll|salary|wage|compensation|pay)\b',
            'leave': r'\b(leave|vacation|sick|absence|time off)\b',
            'compliance': r'\b(compliance|compliant|requirement|mandatory)\b',
            'diversity': r'\b(diversity|equity|inclusion|dei)\b',
            'performance': r'\b(performance|evaluation|review|assessment)\b',
            'recruitment': r'\b(recruitment|recruit|applicant|candidate)\b',
        }
        
        content_lower = content.lower()
        for topic, pattern in topic_patterns.items():
            if re.search(pattern, content_lower, re.IGNORECASE):
                topics.append(topic)
        
        return topics
    
    def build_graph(self, verbose: bool = True) -> KnowledgeGraph:
        """
        Build the complete knowledge graph
        Phase 1: Create nodes and extract hyperlinks
        """
        if verbose:
            print("=" * 80)
            print("Building Knowledge Graph - Phase 1")
            print("=" * 80)
            print()
        
        # Phase 1a: Create all nodes
        if verbose:
            print("Phase 1a: Creating nodes from markdown files...")
        
        md_files = list(self.knowledge_dir.rglob('*.md'))
        total_files = len(md_files)
        
        for idx, md_file in enumerate(md_files, 1):
            if verbose and idx % 500 == 0:
                print(f"  Processing file {idx}/{total_files}...")
            
            try:
                # Get agency from folder structure
                agency = md_file.parent.name
                
                # Extract metadata and content
                metadata = self.extract_metadata(md_file)
                content = self.extract_content(md_file)
                
                # Create node ID (relative path without extension)
                node_id = str(md_file.relative_to(self.knowledge_dir).with_suffix(''))
                
                # Create node
                node = create_node_from_markdown(
                    file_path=node_id,
                    metadata=metadata,
                    content=content,
                    agency=agency
                )
                
                # Extract keywords and topics
                node.keywords = self.extract_keywords(content, node.title)
                node.topics = self.extract_topics(content, agency)
                
                # Add to graph
                self.graph.add_node(node)
                
                # Build URL and filename indexes
                if node.source_url:
                    normalized_url = self.normalize_url(node.source_url)
                    self.url_to_node[normalized_url] = node_id
                
                self.file_to_node[md_file.stem] = node_id
                self.file_to_node[md_file.name] = node_id
                
            except Exception as e:
                if verbose:
                    print(f"  ✗ Error processing {md_file}: {e}")
        
        if verbose:
            print(f"✓ Created {len(self.graph.nodes)} nodes")
            print()
        
        # Phase 1b: Extract hyperlinks and create edges
        if verbose:
            print("Phase 1b: Extracting hyperlinks and creating edges...")
        
        edge_count = 0
        for idx, (node_id, node) in enumerate(self.graph.nodes.items(), 1):
            if verbose and idx % 500 == 0:
                print(f"  Processing links for node {idx}/{len(self.graph.nodes)}...")
            
            try:
                # Read content again to extract links
                md_file = self.knowledge_dir / (node_id + '.md')
                content = self.extract_content(md_file)
                
                # Extract all links
                links = self.extract_links(content)
                
                for link_text, url, context in links:
                    # Try to resolve to a node
                    target_id = self.resolve_link_to_node(url, md_file)
                    
                    if target_id and target_id in self.graph.nodes:
                        # Create edge
                        edge = EdgeMetadata(
                            source_id=node_id,
                            target_id=target_id,
                            edge_type=EdgeType.HYPERLINK,
                            anchor_text=link_text,
                            context=context,
                            weight=1.0,
                            confidence=1.0
                        )
                        self.graph.add_edge(edge)
                        edge_count += 1
                        
            except Exception as e:
                if verbose:
                    print(f"  ✗ Error extracting links from {node_id}: {e}")
        
        if verbose:
            print(f"✓ Created {edge_count} hyperlink edges")
            print()
        
        # Phase 1c: Create agency nodes and link documents to agencies
        if verbose:
            print("Phase 1c: Creating agency nodes and linking documents...")
        
        from network.schema import create_agency_node
        
        agency_nodes_created = 0
        agency_edges = 0
        
        # Create agency nodes and calculate statistics
        for agency, doc_ids in self.graph.agency_index.items():
            # Calculate agency statistics
            total_words = sum(self.graph.nodes[doc_id].word_count for doc_id in doc_ids if doc_id in self.graph.nodes)
            
            # Create agency node
            agency_node = create_agency_node(
                agency_name=agency,
                document_count=len(doc_ids),
                total_words=total_words
            )
            self.graph.add_node(agency_node)
            agency_nodes_created += 1
            
            # Link all documents to their agency
            for doc_id in doc_ids:
                if doc_id in self.graph.nodes:
                    edge = EdgeMetadata(
                        source_id=doc_id,
                        target_id=agency_node.node_id,
                        edge_type=EdgeType.BELONGS_TO_AGENCY,
                        weight=1.0,
                        confidence=1.0
                    )
                    self.graph.add_edge(edge)
                    agency_edges += 1
        
        if verbose:
            print(f"✓ Created {agency_nodes_created} agency nodes")
            print(f"✓ Created {agency_edges} document-to-agency edges")
            print()
        
        # Phase 1d: Create hierarchical edges (parent-child) for index pages
        if verbose:
            print("Phase 1d: Creating hierarchical relationships...")
        
        hierarchy_edges = 0
        for node_id, node in self.graph.nodes.items():
            # Skip agency nodes
            if node.node_type == NodeType.AGENCY_ROOT:
                continue
            
            # Find potential parent (index page in same agency)
            agency_index_id = f"{node.agency}/index"
            
            if agency_index_id in self.graph.nodes and node_id != agency_index_id:
                edge = EdgeMetadata(
                    source_id=agency_index_id,
                    target_id=node_id,
                    edge_type=EdgeType.PARENT_CHILD,
                    weight=0.5,
                    confidence=0.8
                )
                self.graph.add_edge(edge)
                hierarchy_edges += 1
        
        if verbose:
            print(f"✓ Created {hierarchy_edges} hierarchical edges")
            print()
        
        # Phase 1e: Create agency co-membership edges
        if verbose:
            print("Phase 1e: Creating agency co-membership edges...")
        
        agency_edges = 0
        for agency, node_ids in self.graph.agency_index.items():
            # Connect all documents in same agency
            for i, source_id in enumerate(node_ids):
                for target_id in node_ids[i+1:i+6]:  # Limit to avoid too many edges
                    edge = EdgeMetadata(
                        source_id=source_id,
                        target_id=target_id,
                        edge_type=EdgeType.SAME_AGENCY,
                        weight=0.3,
                        confidence=1.0
                    )
                    self.graph.add_edge(edge)
                    agency_edges += 1
        
        if verbose:
            print(f"✓ Created {agency_edges} agency co-membership edges")
            print()
        
        # Update statistics
        self.graph.update_statistics()
        
        # Summary
        if verbose:
            print("=" * 80)
            print("Graph Building Complete - Phase 1")
            print("=" * 80)
            print(f"Total Nodes: {self.graph.total_documents}")
            print(f"Total Edges: {len(self.graph.edges)}")
            print(f"Agencies: {self.graph.total_agencies}")
            print()
            print("Node Types:")
            for node_type, nodes in self.graph.type_index.items():
                print(f"  {node_type.value}: {len(nodes)}")
            print()
            print("Edge Types:")
            edge_type_counts = defaultdict(int)
            for edge in self.graph.edges:
                edge_type_counts[edge.edge_type] += 1
            for edge_type, count in edge_type_counts.items():
                print(f"  {edge_type.value}: {count}")
            print()
        
        return self.graph
    
    def get_graph(self) -> KnowledgeGraph:
        """Get the built graph"""
        return self.graph


def main():
    """Build the graph"""
    builder = GraphBuilder(knowledge_dir="knowledge")
    graph = builder.build_graph(verbose=True)
    
    print("\nGraph building complete!")
    print(f"Graph contains {graph.total_documents} documents across {graph.total_agencies} agencies")
    print(f"Created {len(graph.edges)} relationships")


if __name__ == "__main__":
    main()
