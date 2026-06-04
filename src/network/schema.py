"""
Network Schema Definition
Defines the data model for the document knowledge graph
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
from enum import Enum


class NodeType(Enum):
    """Types of nodes in the knowledge graph"""
    HTML_PAGE = "html_page"
    PDF_DOCUMENT = "pdf_document"
    DOCX_DOCUMENT = "docx_document"
    INDEX_PAGE = "index_page"
    POLICY_PAGE = "policy_page"
    PROGRAM_PAGE = "program_page"
    AGENCY_ROOT = "agency_root"
    TOPIC_CLUSTER = "topic_cluster"


class EdgeType(Enum):
    """Types of relationships between nodes"""
    HYPERLINK = "hyperlink"              # Direct hyperlink from A to B
    CITATION = "citation"                # Document A cites/references B
    PARENT_CHILD = "parent_child"        # Hierarchical relationship
    SEMANTIC_SIMILAR = "semantic_similar" # Content similarity
    TOPIC_RELATED = "topic_related"      # Share common topics/keywords
    SAME_AGENCY = "same_agency"          # Same agency affiliation
    BELONGS_TO_AGENCY = "belongs_to_agency"  # Document belongs to agency
    TEMPORAL = "temporal"                # Time-based relationship (e.g., updates)


@dataclass
class NodeMetadata:
    """Metadata for each document node"""
    # Core identification
    node_id: str                         # Unique identifier (relative file path)
    title: str                           # Document title
    node_type: NodeType                  # Type of document
    
    # Source information
    source_url: str                      # Original URL
    file_path: str                       # Local file path
    agency: str                          # Agency name (folder)
    
    # Content metadata
    crawled_date: Optional[datetime] = None
    content_hash: Optional[str] = None   # Hash of content for change detection
    word_count: int = 0
    chunk_count: int = 0                 # Number of content chunks
    
    # Network metrics (computed)
    pagerank_score: float = 0.0
    betweenness_centrality: float = 0.0
    in_degree: int = 0                   # Number of incoming links
    out_degree: int = 0                  # Number of outgoing links
    
    # Content features
    topics: List[str] = field(default_factory=list)      # Extracted topics
    entities: List[str] = field(default_factory=list)    # Named entities
    keywords: List[str] = field(default_factory=list)    # Key terms
    
    # RAG optimization
    has_embeddings: bool = False
    chunk_ids: List[str] = field(default_factory=list)   # IDs of content chunks
    
    # Additional properties
    custom_properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EdgeMetadata:
    """Metadata for relationships between documents"""
    source_id: str                       # Source node ID
    target_id: str                       # Target node ID
    edge_type: EdgeType                  # Type of relationship
    
    # Edge properties
    weight: float = 1.0                  # Relationship strength (0-1)
    confidence: float = 1.0              # Confidence in relationship (0-1)
    
    # Context information
    anchor_text: Optional[str] = None    # Link text (for hyperlinks)
    context: Optional[str] = None        # Surrounding text context
    
    # Additional properties
    created_date: Optional[datetime] = None
    custom_properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContentChunk:
    """Represents a semantic chunk of document content for RAG"""
    chunk_id: str                        # Unique chunk identifier
    document_id: str                     # Parent document ID
    content: str                         # Chunk text content
    
    # Chunk metadata
    chunk_index: int                     # Position in document (0-based)
    start_position: int = 0              # Character offset in original
    end_position: int = 0
    
    # Embeddings
    embedding: Optional[List[float]] = None  # Vector embedding
    embedding_model: Optional[str] = None    # Model used for embedding
    
    # Context
    section_title: Optional[str] = None      # Section/heading this belongs to
    chunk_type: str = "text"                 # text, table, list, code, etc.
    
    # Custom properties
    custom_properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeGraph:
    """Complete knowledge graph structure"""
    # Core graph data
    nodes: Dict[str, NodeMetadata] = field(default_factory=dict)
    edges: List[EdgeMetadata] = field(default_factory=list)
    chunks: Dict[str, ContentChunk] = field(default_factory=dict)
    
    # Graph metadata
    created_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    version: str = "1.0"
    
    # Statistics
    total_documents: int = 0
    total_agencies: int = 0
    total_chunks: int = 0
    
    # Indexes for fast lookup
    agency_index: Dict[str, List[str]] = field(default_factory=dict)  # agency -> node_ids
    type_index: Dict[NodeType, List[str]] = field(default_factory=dict)  # type -> node_ids
    topic_index: Dict[str, List[str]] = field(default_factory=dict)  # topic -> node_ids
    
    # Graph statistics
    graph_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def add_node(self, node: NodeMetadata) -> None:
        """Add a node to the graph"""
        self.nodes[node.node_id] = node
        
        # Update indexes
        if node.agency not in self.agency_index:
            self.agency_index[node.agency] = []
        self.agency_index[node.agency].append(node.node_id)
        
        if node.node_type not in self.type_index:
            self.type_index[node.node_type] = []
        self.type_index[node.node_type].append(node.node_id)
        
        for topic in node.topics:
            if topic not in self.topic_index:
                self.topic_index[topic] = []
            self.topic_index[topic].append(node.node_id)
    
    def add_edge(self, edge: EdgeMetadata) -> None:
        """Add an edge to the graph"""
        self.edges.append(edge)
        
        # Update node degrees
        if edge.source_id in self.nodes:
            self.nodes[edge.source_id].out_degree += 1
        if edge.target_id in self.nodes:
            self.nodes[edge.target_id].in_degree += 1
    
    def add_chunk(self, chunk: ContentChunk) -> None:
        """Add a content chunk to the graph"""
        self.chunks[chunk.chunk_id] = chunk
        
        # Update parent document's chunk list
        if chunk.document_id in self.nodes:
            self.nodes[chunk.document_id].chunk_ids.append(chunk.chunk_id)
            self.nodes[chunk.document_id].chunk_count += 1
    
    def get_neighbors(self, node_id: str, edge_type: Optional[EdgeType] = None) -> List[str]:
        """Get all neighboring nodes"""
        neighbors = []
        for edge in self.edges:
            if edge.source_id == node_id:
                if edge_type is None or edge.edge_type == edge_type:
                    neighbors.append(edge.target_id)
        return neighbors
    
    def get_by_agency(self, agency: str) -> List[NodeMetadata]:
        """Get all nodes for a specific agency"""
        node_ids = self.agency_index.get(agency, [])
        return [self.nodes[nid] for nid in node_ids if nid in self.nodes]
    
    def get_by_type(self, node_type: NodeType) -> List[NodeMetadata]:
        """Get all nodes of a specific type"""
        node_ids = self.type_index.get(node_type, [])
        return [self.nodes[nid] for nid in node_ids if nid in self.nodes]
    
    def get_by_topic(self, topic: str) -> List[NodeMetadata]:
        """Get all nodes related to a topic"""
        node_ids = self.topic_index.get(topic, [])
        return [self.nodes[nid] for nid in node_ids if nid in self.nodes]
    
    def update_statistics(self) -> None:
        """Update graph statistics"""
        self.total_documents = len(self.nodes)
        self.total_agencies = len(self.agency_index)
        self.total_chunks = len(self.chunks)
        self.last_updated = datetime.now()


# Query result structure for RAG
@dataclass
class RAGResult:
    """Result from a RAG query"""
    query: str
    results: List[Dict[str, Any]]        # Ranked results
    total_found: int
    search_strategy: str                 # How results were found
    execution_time_ms: float
    
    # Context expansion
    expanded_nodes: List[str] = field(default_factory=list)  # Additional context nodes
    path_to_results: Dict[str, List[str]] = field(default_factory=dict)  # Paths in graph


def create_node_from_markdown(
    file_path: str,
    metadata: Dict[str, str],
    content: str,
    agency: str
) -> NodeMetadata:
    """Factory function to create a node from markdown file"""
    from pathlib import Path
    import hashlib
    
    # Determine node type
    filename = Path(file_path).name
    if filename.startswith('pdf_'):
        node_type = NodeType.PDF_DOCUMENT
    elif filename.startswith('_docs_'):
        node_type = NodeType.DOCX_DOCUMENT
    elif 'index' in filename.lower():
        node_type = NodeType.INDEX_PAGE
    elif 'policy' in filename.lower() or 'Policy' in metadata.get('title', ''):
        node_type = NodeType.POLICY_PAGE
    elif 'program' in filename.lower() or 'Program' in metadata.get('title', ''):
        node_type = NodeType.PROGRAM_PAGE
    else:
        node_type = NodeType.HTML_PAGE
    
    # Create content hash
    content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
    
    # Parse crawled date
    crawled_date = None
    if 'crawled' in metadata:
        try:
            crawled_date = datetime.strptime(metadata['crawled'], '%Y-%m-%d %H:%M:%S')
        except:
            pass
    
    # Count words
    word_count = len(content.split())
    
    return NodeMetadata(
        node_id=file_path,
        title=metadata.get('title', Path(file_path).stem),
        node_type=node_type,
        source_url=metadata.get('source', ''),
        file_path=file_path,
        agency=agency,
        crawled_date=crawled_date,
        content_hash=content_hash,
        word_count=word_count
    )


def create_agency_node(
    agency_name: str,
    document_count: int = 0,
    total_words: int = 0
) -> NodeMetadata:
    """Factory function to create an agency root node"""
    return NodeMetadata(
        node_id=f"_agency_{agency_name}",
        title=f"{agency_name.replace('-', ' ').replace('_', ' ').title()}",
        node_type=NodeType.AGENCY_ROOT,
        source_url="",
        file_path=f"_agency_{agency_name}",
        agency=agency_name,
        word_count=total_words,
        custom_properties={
            "document_count": document_count,
            "is_agency_node": True
        }
    )
