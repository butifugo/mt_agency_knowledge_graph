"""
Semantic Analyzer
Adds semantic relationships to knowledge graphs
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.shared.schemas import KnowledgeEdge, EdgeType


class SemanticAnalyzer:
    """Adds semantic similarity edges to knowledge graphs"""
    
    def __init__(self, knowledge_file: str):
        """
        Initialize semantic analyzer
        
        Args:
            knowledge_file: Path to knowledge graph JSON file
        """
        self.knowledge_file = Path(knowledge_file)
        
        with open(self.knowledge_file, 'r') as f:
            self.graph_data = json.load(f)
        
        self.nodes = self.graph_data['nodes']
        self.edges = self.graph_data['edges']
    
    def _compute_simple_similarity(self, keywords1: List[str], keywords2: List[str]) -> float:
        """Compute Jaccard similarity between keyword sets"""
        if not keywords1 or not keywords2:
            return 0.0
        
        set1 = set(keywords1)
        set2 = set(keywords2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def add_semantic_edges(self, threshold: float = 0.3, verbose: bool = True):
        """
        Add semantic similarity edges between documents
        
        Args:
            threshold: Minimum similarity score to create edge
            verbose: Print progress
        """
        if verbose:
            print(f"\nAdding semantic similarity edges...")
            print(f"  Similarity threshold: {threshold}")
        
        node_ids = list(self.nodes.keys())
        semantic_edges = []
        
        for i, node_id1 in enumerate(node_ids):
            node1 = self.nodes[node_id1]
            keywords1 = node1.get('keywords', [])
            
            for node_id2 in node_ids[i+1:]:
                node2 = self.nodes[node_id2]
                keywords2 = node2.get('keywords', [])
                
                # Compute similarity
                similarity = self._compute_simple_similarity(keywords1, keywords2)
                
                if similarity >= threshold:
                    # Create bidirectional edges
                    edge1 = {
                        'source': node_id1,
                        'target': node_id2,
                        'type': EdgeType.SEMANTIC_SIMILAR.value,
                        'weight': similarity,
                        'metadata': {'similarity_score': similarity}
                    }
                    edge2 = {
                        'source': node_id2,
                        'target': node_id1,
                        'type': EdgeType.SEMANTIC_SIMILAR.value,
                        'weight': similarity,
                        'metadata': {'similarity_score': similarity}
                    }
                    
                    semantic_edges.append(edge1)
                    semantic_edges.append(edge2)
        
        # Add to graph
        self.edges.extend(semantic_edges)
        self.graph_data['edges'] = self.edges
        
        # Update statistics
        stats = self.graph_data.get('statistics', {})
        stats['semantic_edges'] = len(semantic_edges)
        stats['total_edges'] = len(self.edges)
        self.graph_data['statistics'] = stats
        
        if verbose:
            print(f"  ✓ Added {len(semantic_edges)} semantic similarity edges")
        
        return len(semantic_edges)
    
    def add_topic_edges(self, verbose: bool = True):
        """
        Add topic-based edges by grouping documents with similar keywords
        
        Args:
            verbose: Print progress
        """
        if verbose:
            print(f"\nAdding topic clustering edges...")
        
        # Group documents by shared keywords
        keyword_to_docs = defaultdict(list)
        
        for node_id, node in self.nodes.items():
            keywords = node.get('keywords', [])
            for keyword in keywords[:5]:  # Use top 5 keywords
                keyword_to_docs[keyword].append(node_id)
        
        # Create topic edges for documents sharing keywords
        topic_edges = []
        
        for keyword, doc_ids in keyword_to_docs.items():
            if len(doc_ids) < 2:
                continue
            
            # Create edges between documents in same topic cluster
            for i, doc_id1 in enumerate(doc_ids):
                for doc_id2 in doc_ids[i+1:]:
                    edge = {
                        'source': doc_id1,
                        'target': doc_id2,
                        'type': EdgeType.TOPIC_RELATED.value,
                        'weight': 0.5,
                        'metadata': {'shared_topic': keyword}
                    }
                    topic_edges.append(edge)
        
        # Add to graph
        self.edges.extend(topic_edges)
        self.graph_data['edges'] = self.edges
        
        # Update statistics
        stats = self.graph_data.get('statistics', {})
        stats['topic_edges'] = len(topic_edges)
        stats['total_edges'] = len(self.edges)
        stats['topic_clusters'] = len([k for k, v in keyword_to_docs.items() if len(v) >= 2])
        self.graph_data['statistics'] = stats
        
        if verbose:
            print(f"  ✓ Added {len(topic_edges)} topic clustering edges")
            print(f"  ✓ Identified {stats['topic_clusters']} topic clusters")
        
        return len(topic_edges)
    
    def save_enhanced_graph(self, output_file: Optional[str] = None):
        """Save enhanced graph with semantic edges"""
        if output_file is None:
            output_file = str(self.knowledge_file)
        
        output_path = Path(output_file)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.graph_data, f, indent=2, ensure_ascii=False)
        
        return output_path
