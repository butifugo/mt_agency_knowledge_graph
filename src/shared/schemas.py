"""
Data Schemas for Knowledge Network
Defines data models used across all phases
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import hashlib


class NodeType(Enum):
    """Types of nodes in graphs"""
    HTML_PAGE = "html_page"
    PDF_DOCUMENT = "pdf_document"
    DOCX_DOCUMENT = "docx_document"
    INDEX_PAGE = "index_page"
    AGENCY_ROOT = "agency_root"
    TOPIC_CLUSTER = "topic_cluster"


class EdgeType(Enum):
    """Types of relationships"""
    HYPERLINK = "hyperlink"
    DOCUMENT_LINK = "document_link"
    SEMANTIC_SIMILAR = "semantic_similar"
    TOPIC_RELATED = "topic_related"
    PARENT_CHILD = "parent_child"
    SAME_AGENCY = "same_agency"


@dataclass
class Document:
    """Core document representation"""
    id: str
    url: str
    title: str
    content: str
    mime_type: str
    file_path: str
    agency: str
    crawled_date: datetime
    word_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            # Generate ID from URL hash
            self.id = hashlib.md5(self.url.encode()).hexdigest()[:12]


@dataclass
class KnowledgeNode:
    """Node in knowledge graph"""
    id: str
    document: Document
    topics: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    embeddings: Optional[Any] = None
    pagerank: float = 0.0
    centrality: float = 0.0
    in_degree: int = 0
    out_degree: int = 0
    node_type: NodeType = NodeType.HTML_PAGE


@dataclass
class KnowledgeEdge:
    """Edge in knowledge graph"""
    source: str
    target: str
    edge_type: EdgeType
    weight: float = 1.0
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NavigationNode:
    """Node in navigation graph"""
    id: str
    url: str
    title: str
    node_type: str  # html_page, pdf_document, docx_document
    mime_type: str
    level: int  # Depth in hierarchy
    parent: Optional[str] = None
    children: List[str] = field(default_factory=list)
    file_path: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NavigationEdge:
    """Edge in navigation graph"""
    source: str
    target: str
    link_text: str
    edge_type: str  # hyperlink, document_link
    context: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
