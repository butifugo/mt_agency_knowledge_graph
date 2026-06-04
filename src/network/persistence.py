"""
Persistence Layer - Phase 3
Saves and loads the knowledge graph in multiple formats
Supports JSON, GraphML, and pickle formats
"""

import json
import pickle
from pathlib import Path
from typing import Optional
from datetime import datetime
import networkx as nx

from src.network.schema import KnowledgeGraph, NodeType, EdgeType


class GraphPersistence:
    """Handles saving and loading knowledge graphs"""
    
    def __init__(self, output_dir: str = "src/network/exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def save_json(self, graph: KnowledgeGraph, filename: str = "knowledge_graph.json", verbose: bool = True) -> str:
        """Save graph as JSON (human-readable, for visualization)"""
        filepath = self.output_dir / filename
        
        if verbose:
            print(f"Saving graph to JSON: {filepath}")
        
        # Convert graph to JSON-serializable format
        data = {
            "metadata": {
                "created": graph.created_date.isoformat() if graph.created_date else None,
                "updated": graph.last_updated.isoformat() if graph.last_updated else None,
                "version": graph.version,
                "total_documents": graph.total_documents,
                "total_agencies": graph.total_agencies,
                "total_chunks": graph.total_chunks,
                "statistics": graph.graph_metrics
            },
            "nodes": [],
            "edges": [],
            "agencies": list(graph.agency_index.keys())
        }
        
        # Add nodes
        for node_id, node in graph.nodes.items():
            data["nodes"].append({
                "id": node.node_id,
                "title": node.title,
                "type": node.node_type.value,
                "source_url": node.source_url,
                "agency": node.agency,
                "word_count": node.word_count,
                "chunk_count": node.chunk_count,
                "pagerank": node.pagerank_score,
                "betweenness": node.betweenness_centrality,
                "in_degree": node.in_degree,
                "out_degree": node.out_degree,
                "topics": node.topics,
                "keywords": node.keywords[:10],  # Top 10 keywords
                "crawled_date": node.crawled_date.isoformat() if node.crawled_date else None
            })
        
        # Add edges
        for edge in graph.edges:
            data["edges"].append({
                "source": edge.source_id,
                "target": edge.target_id,
                "type": edge.edge_type.value,
                "weight": edge.weight,
                "confidence": edge.confidence,
                "anchor_text": edge.anchor_text,
                "context": edge.context[:100] if edge.context else None  # Truncate context
            })
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        if verbose:
            print(f"✓ Saved {len(data['nodes'])} nodes and {len(data['edges'])} edges to JSON")
        
        return str(filepath)
    
    def save_graphml(self, graph: KnowledgeGraph, filename: str = "knowledge_graph.graphml", verbose: bool = True) -> str:
        """Save graph as GraphML (for Gephi, Cytoscape, etc.)"""
        filepath = self.output_dir / filename
        
        if verbose:
            print(f"Saving graph to GraphML: {filepath}")
        
        # Create NetworkX graph
        G = nx.DiGraph()
        
        # Add nodes with attributes
        for node_id, node in graph.nodes.items():
            G.add_node(
                node_id,
                title=node.title,
                type=node.node_type.value,
                source_url=node.source_url,
                agency=node.agency,
                word_count=node.word_count,
                chunk_count=node.chunk_count,
                pagerank=node.pagerank_score,
                betweenness=node.betweenness_centrality,
                in_degree=node.in_degree,
                out_degree=node.out_degree,
                topics=",".join(node.topics),
                keywords=",".join(node.keywords[:10])
            )
        
        # Add edges with attributes
        for edge in graph.edges:
            G.add_edge(
                edge.source_id,
                edge.target_id,
                type=edge.edge_type.value,
                weight=edge.weight,
                confidence=edge.confidence,
                anchor_text=edge.anchor_text or "",
                context=edge.context[:100] if edge.context else ""
            )
        
        # Write to GraphML
        nx.write_graphml(G, filepath)
        
        if verbose:
            print(f"✓ Saved graph to GraphML format")
        
        return str(filepath)
    
    def save_pickle(self, graph: KnowledgeGraph, filename: str = "knowledge_graph.pkl", verbose: bool = True) -> str:
        """Save complete graph as pickle (fastest, preserves all Python objects)"""
        filepath = self.output_dir / filename
        
        if verbose:
            print(f"Saving graph to pickle: {filepath}")
        
        with open(filepath, 'wb') as f:
            pickle.dump(graph, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        if verbose:
            print(f"✓ Saved complete graph to pickle")
        
        return str(filepath)
    
    def save_chunks_json(self, graph: KnowledgeGraph, filename: str = "content_chunks.json", verbose: bool = True) -> str:
        """Save content chunks separately for RAG (without embeddings to reduce size)"""
        filepath = self.output_dir / filename
        
        if verbose:
            print(f"Saving content chunks to JSON: {filepath}")
        
        chunks_data = []
        for chunk_id, chunk in graph.chunks.items():
            chunks_data.append({
                "id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "section_title": chunk.section_title,
                "chunk_type": chunk.chunk_type,
                "has_embedding": chunk.embedding is not None
            })
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, indent=2, ensure_ascii=False)
        
        if verbose:
            print(f"✓ Saved {len(chunks_data)} content chunks to JSON")
        
        return str(filepath)
    
    def save_all(self, graph: KnowledgeGraph, prefix: str = "knowledge_graph", verbose: bool = True):
        """Save graph in all formats"""
        if verbose:
            print("=" * 80)
            print("Saving Knowledge Graph - Phase 3")
            print("=" * 80)
            print()
        
        files = {}
        
        # Save JSON
        files['json'] = self.save_json(graph, f"{prefix}.json", verbose=verbose)
        print()
        
        # Save GraphML
        files['graphml'] = self.save_graphml(graph, f"{prefix}.graphml", verbose=verbose)
        print()
        
        # Save pickle
        files['pickle'] = self.save_pickle(graph, f"{prefix}.pkl", verbose=verbose)
        print()
        
        # Save chunks
        if graph.total_chunks > 0:
            files['chunks'] = self.save_chunks_json(graph, f"{prefix}_chunks.json", verbose=verbose)
            print()
        
        if verbose:
            print("=" * 80)
            print("Graph Persistence Complete - Phase 3")
            print("=" * 80)
            print("\nSaved files:")
            for format_name, filepath in files.items():
                file_size = Path(filepath).stat().st_size / (1024 * 1024)  # MB
                print(f"  {format_name.upper()}: {filepath} ({file_size:.2f} MB)")
            print()
        
        return files
    
    def load_pickle(self, filename: str = "knowledge_graph.pkl", verbose: bool = True) -> Optional[KnowledgeGraph]:
        """Load graph from pickle file"""
        filepath = self.output_dir / filename
        
        if not filepath.exists():
            if verbose:
                print(f"✗ File not found: {filepath}")
            return None
        
        if verbose:
            print(f"Loading graph from pickle: {filepath}")
        
        with open(filepath, 'rb') as f:
            graph = pickle.load(f)
        
        if verbose:
            print(f"✓ Loaded graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
        
        return graph
    
    def load_json(self, filename: str = "knowledge_graph.json", verbose: bool = True) -> Optional[dict]:
        """Load graph from JSON file (returns raw dict, not KnowledgeGraph object)"""
        filepath = self.output_dir / filename
        
        if not filepath.exists():
            if verbose:
                print(f"✗ File not found: {filepath}")
            return None
        
        if verbose:
            print(f"Loading graph from JSON: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if verbose:
            print(f"✓ Loaded {len(data['nodes'])} nodes and {len(data['edges'])} edges")
        
        return data


def main():
    """Test persistence layer"""
    from network.graph_builder import GraphBuilder
    from network.semantic_layer import SemanticEnhancer
    
    print("Building graph...")
    builder = GraphBuilder(knowledge_dir="knowledge")
    graph = builder.build_graph(verbose=False)
    
    print("Enhancing with semantic layer...")
    enhancer = SemanticEnhancer(graph, knowledge_dir="knowledge")
    graph = enhancer.enhance_graph(
        create_chunks_flag=True,
        add_semantic_edges_flag=False,
        add_topic_edges_flag=True,
        verbose=False
    )
    
    print(f"Graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges, {graph.total_chunks} chunks")
    print()
    
    # Save in all formats
    persistence = GraphPersistence(output_dir="src/network/exports")
    files = persistence.save_all(graph, prefix="montana_knowledge", verbose=True)
    
    print("\nTesting load...")
    loaded_graph = persistence.load_pickle("montana_knowledge.pkl", verbose=True)
    
    if loaded_graph:
        print(f"\n✓ Successfully loaded graph!")
        print(f"  Nodes: {len(loaded_graph.nodes)}")
        print(f"  Edges: {len(loaded_graph.edges)}")
        print(f"  Chunks: {len(loaded_graph.chunks)}")


if __name__ == "__main__":
    main()
