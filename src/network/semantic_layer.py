"""
Semantic Layer - Phase 2
Adds semantic similarity relationships using embeddings
Creates content chunks for RAG and computes document similarity
"""

import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import hashlib
import re
from collections import defaultdict

from src.network.schema import (
    KnowledgeGraph, EdgeMetadata, ContentChunk,
    EdgeType, NodeType
)


class SemanticEnhancer:
    """Adds semantic relationships to the knowledge graph"""
    
    def __init__(self, graph: KnowledgeGraph, knowledge_dir: str = "knowledge"):
        self.graph = graph
        self.knowledge_dir = Path(knowledge_dir)
        self.embeddings_cache: Dict[str, np.ndarray] = {}
        
    def chunk_content(self, content: str, node_id: str, chunk_size: int = 512) -> List[ContentChunk]:
        """
        Split document content into semantic chunks for RAG
        Uses paragraph-aware chunking with overlap
        """
        chunks = []
        
        # Split by paragraphs (double newlines)
        paragraphs = re.split(r'\n\s*\n', content)
        
        current_chunk = ""
        current_position = 0
        chunk_index = 0
        current_section = None
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Detect section headers (markdown headings)
            if para.startswith('#'):
                current_section = para.lstrip('#').strip()
            
            # If adding this paragraph exceeds chunk size, save current chunk
            if current_chunk and len(current_chunk) + len(para) > chunk_size:
                chunk_id = f"{node_id}::chunk_{chunk_index}"
                
                chunk = ContentChunk(
                    chunk_id=chunk_id,
                    document_id=node_id,
                    content=current_chunk.strip(),
                    chunk_index=chunk_index,
                    start_position=current_position,
                    end_position=current_position + len(current_chunk),
                    section_title=current_section,
                    chunk_type='text'
                )
                chunks.append(chunk)
                
                chunk_index += 1
                current_position += len(current_chunk)
                
                # Start new chunk with overlap (last sentence of previous chunk)
                sentences = current_chunk.split('. ')
                if len(sentences) > 1:
                    current_chunk = sentences[-1] + '. ' + para
                else:
                    current_chunk = para
            else:
                if current_chunk:
                    current_chunk += '\n\n' + para
                else:
                    current_chunk = para
        
        # Add final chunk
        if current_chunk:
            chunk_id = f"{node_id}::chunk_{chunk_index}"
            chunk = ContentChunk(
                chunk_id=chunk_id,
                document_id=node_id,
                content=current_chunk.strip(),
                chunk_index=chunk_index,
                start_position=current_position,
                end_position=current_position + len(current_chunk),
                section_title=current_section,
                chunk_type='text'
            )
            chunks.append(chunk)
        
        return chunks
    
    def compute_simple_embedding(self, text: str, dim: int = 128) -> np.ndarray:
        """
        Compute a simple embedding using TF-IDF-like approach
        This is a placeholder - can be replaced with actual embeddings (OpenAI, sentence-transformers, etc.)
        """
        # Simple bag-of-words + hashing for demo purposes
        # In production, use: sentence-transformers, OpenAI embeddings, etc.
        
        # Clean text
        text_lower = text.lower()
        words = re.findall(r'\b[a-z]{3,}\b', text_lower)
        
        # Create embedding using word hashing
        embedding = np.zeros(dim)
        for word in words:
            # Hash word to dimension index
            hash_val = int(hashlib.md5(word.encode()).hexdigest(), 16)
            idx = hash_val % dim
            embedding[idx] += 1
        
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def get_document_embedding(self, node_id: str) -> Optional[np.ndarray]:
        """Get or compute embedding for a document"""
        if node_id in self.embeddings_cache:
            return self.embeddings_cache[node_id]
        
        try:
            # Read document content
            md_file = self.knowledge_dir / (node_id + '.md')
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remove frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    content = parts[2]
            
            # Compute embedding
            embedding = self.compute_simple_embedding(content)
            self.embeddings_cache[node_id] = embedding
            
            return embedding
        except Exception as e:
            return None
    
    def create_chunks(self, verbose: bool = True) -> int:
        """Create content chunks for all documents"""
        if verbose:
            print("Phase 2a: Creating content chunks for RAG...")
        
        total_chunks = 0
        
        for idx, (node_id, node) in enumerate(self.graph.nodes.items(), 1):
            if verbose and idx % 1000 == 0:
                print(f"  Chunking document {idx}/{len(self.graph.nodes)}...")
            
            try:
                # Read document content
                md_file = self.knowledge_dir / (node_id + '.md')
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Remove frontmatter
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        content = parts[2]
                
                # Create chunks
                chunks = self.chunk_content(content, node_id, chunk_size=512)
                
                # Add chunks to graph
                for chunk in chunks:
                    self.graph.add_chunk(chunk)
                    total_chunks += 1
                
            except Exception as e:
                if verbose:
                    print(f"  ✗ Error chunking {node_id}: {e}")
        
        if verbose:
            print(f"✓ Created {total_chunks} content chunks")
            print()
        
        return total_chunks
    
    def add_semantic_edges(self, similarity_threshold: float = 0.3, max_edges_per_node: int = 10, verbose: bool = True):
        """
        Add semantic similarity edges between documents
        Uses embeddings to find similar documents
        """
        if verbose:
            print("Phase 2b: Computing semantic similarities...")
        
        # Compute embeddings for all documents
        if verbose:
            print("  Computing document embeddings...")
        
        node_ids = list(self.graph.nodes.keys())
        embeddings = {}
        
        for idx, node_id in enumerate(node_ids, 1):
            if verbose and idx % 1000 == 0:
                print(f"    Processed {idx}/{len(node_ids)} documents...")
            
            embedding = self.get_document_embedding(node_id)
            if embedding is not None:
                embeddings[node_id] = embedding
        
        if verbose:
            print(f"  ✓ Computed {len(embeddings)} embeddings")
            print()
        
        # Find similar documents
        if verbose:
            print("  Finding similar document pairs...")
        
        edge_count = 0
        processed = 0
        
        for idx, node_id in enumerate(node_ids, 1):
            if node_id not in embeddings:
                continue
            
            if verbose and idx % 500 == 0:
                print(f"    Comparing document {idx}/{len(node_ids)}...")
            
            # Get embedding for this document
            emb1 = embeddings[node_id]
            
            # Compare with all other documents
            similarities = []
            for other_id in node_ids:
                if other_id == node_id or other_id not in embeddings:
                    continue
                
                emb2 = embeddings[other_id]
                similarity = self.cosine_similarity(emb1, emb2)
                
                if similarity >= similarity_threshold:
                    similarities.append((other_id, similarity))
            
            # Sort by similarity and take top N
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_similar = similarities[:max_edges_per_node]
            
            # Create edges
            for target_id, similarity in top_similar:
                edge = EdgeMetadata(
                    source_id=node_id,
                    target_id=target_id,
                    edge_type=EdgeType.SEMANTIC_SIMILAR,
                    weight=similarity,
                    confidence=similarity
                )
                self.graph.add_edge(edge)
                edge_count += 1
            
            processed += 1
        
        if verbose:
            print(f"✓ Created {edge_count} semantic similarity edges")
            print()
        
        return edge_count
    
    def add_topic_edges(self, verbose: bool = True) -> int:
        """Add topic-based relationships between documents"""
        if verbose:
            print("Phase 2c: Creating topic-based relationships...")
        
        edge_count = 0
        
        # Group documents by shared topics
        topic_docs = defaultdict(list)
        for node_id, node in self.graph.nodes.items():
            for topic in node.topics:
                topic_docs[topic].append(node_id)
        
        # Create edges between documents with shared topics
        for topic, doc_list in topic_docs.items():
            if len(doc_list) <= 1:
                continue
            
            # Connect documents with shared topic (limit connections to avoid explosion)
            for i, source_id in enumerate(doc_list):
                # Connect to next 3 documents with same topic
                for target_id in doc_list[i+1:i+4]:
                    if source_id != target_id:
                        edge = EdgeMetadata(
                            source_id=source_id,
                            target_id=target_id,
                            edge_type=EdgeType.TOPIC_RELATED,
                            weight=0.5,
                            confidence=0.7,
                            context=f"Shared topic: {topic}"
                        )
                        self.graph.add_edge(edge)
                        edge_count += 1
        
        if verbose:
            print(f"✓ Created {edge_count} topic-based edges")
            print()
        
        return edge_count
    
    def enhance_graph(self, 
                     create_chunks_flag: bool = True,
                     add_semantic_edges_flag: bool = True,
                     add_topic_edges_flag: bool = True,
                     similarity_threshold: float = 0.3,
                     verbose: bool = True) -> KnowledgeGraph:
        """Run all semantic enhancement phases"""
        if verbose:
            print("=" * 80)
            print("Semantic Enhancement - Phase 2")
            print("=" * 80)
            print()
        
        if create_chunks_flag:
            self.create_chunks(verbose=verbose)
        
        if add_semantic_edges_flag:
            self.add_semantic_edges(
                similarity_threshold=similarity_threshold,
                max_edges_per_node=10,
                verbose=verbose
            )
        
        if add_topic_edges_flag:
            self.add_topic_edges(verbose=verbose)
        
        # Update graph statistics
        self.graph.update_statistics()
        
        if verbose:
            print("=" * 80)
            print("Semantic Enhancement Complete - Phase 2")
            print("=" * 80)
            print(f"Total Chunks: {self.graph.total_chunks}")
            print(f"Total Edges: {len(self.graph.edges)}")
            print()
            print("Edge Types:")
            edge_type_counts = defaultdict(int)
            for edge in self.graph.edges:
                edge_type_counts[edge.edge_type] += 1
            for edge_type, count in edge_type_counts.items():
                print(f"  {edge_type.value}: {count}")
            print()
        
        return self.graph


def main():
    """Run semantic enhancement on existing graph"""
    from network.graph_builder import GraphBuilder
    
    print("Building base graph...")
    builder = GraphBuilder(knowledge_dir="knowledge")
    graph = builder.build_graph(verbose=False)
    
    print(f"\nBase graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
    print()
    
    # Enhance with semantic layer
    enhancer = SemanticEnhancer(graph, knowledge_dir="knowledge")
    enhanced_graph = enhancer.enhance_graph(
        create_chunks_flag=True,
        add_semantic_edges_flag=True,  # Set to False for faster testing
        add_topic_edges_flag=True,
        similarity_threshold=0.3,
        verbose=True
    )
    
    print("\nSemantic enhancement complete!")
    print(f"Enhanced graph: {len(enhanced_graph.nodes)} nodes, {len(enhanced_graph.edges)} edges")
    print(f"Content chunks: {enhanced_graph.total_chunks}")


if __name__ == "__main__":
    main()
