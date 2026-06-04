"""
RAG Retriever - Phase 4
Graph-enhanced retrieval for RAG systems
Combines keyword search, semantic search, and graph traversal
"""

import re
import time
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict, Counter
import heapq

from src.network.schema import KnowledgeGraph, RAGResult, NodeType, EdgeType


class GraphRAGRetriever:
    """Retrieves relevant documents and chunks using graph structure"""
    
    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph
        
        # Build inverted index for keyword search
        self.keyword_index: Dict[str, Set[str]] = defaultdict(set)
        self._build_keyword_index()
    
    def _build_keyword_index(self):
        """Build inverted index mapping keywords to document IDs"""
        for node_id, node in self.graph.nodes.items():
            # Index keywords
            for keyword in node.keywords:
                self.keyword_index[keyword.lower()].add(node_id)
            
            # Index topics
            for topic in node.topics:
                self.keyword_index[topic.lower()].add(node_id)
            
            # Index title words
            title_words = re.findall(r'\b\w{3,}\b', node.title.lower())
            for word in title_words:
                self.keyword_index[word].add(node_id)
    
    def keyword_search(self, query: str, top_k: int = 20) -> List[Tuple[str, float]]:
        """
        Basic keyword search
        Returns: List of (node_id, score) tuples
        """
        query_words = re.findall(r'\b\w{3,}\b', query.lower())
        
        # Count matches per document
        doc_scores: Dict[str, int] = defaultdict(int)
        for word in query_words:
            if word in self.keyword_index:
                for node_id in self.keyword_index[word]:
                    doc_scores[node_id] += 1
        
        # Sort by score
        ranked = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Normalize scores
        max_score = ranked[0][1] if ranked else 1
        normalized = [(node_id, score / max_score) for node_id, score in ranked[:top_k]]
        
        return normalized
    
    def expand_via_graph(
        self,
        seed_nodes: List[str],
        max_hops: int = 2,
        max_neighbors: int = 10,
        edge_types: Optional[List[EdgeType]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Expand from seed nodes via graph traversal
        Returns: Dict of {node_id: {distance, path, score}}
        """
        # BFS from seed nodes
        visited = {}
        queue = [(node_id, 0, [node_id], 1.0) for node_id in seed_nodes]
        
        for node_id in seed_nodes:
            visited[node_id] = {
                'distance': 0,
                'path': [node_id],
                'score': 1.0
            }
        
        while queue:
            current_id, dist, path, score = queue.pop(0)
            
            if dist >= max_hops:
                continue
            
            # Get neighbors
            neighbors = []
            for edge in self.graph.edges:
                if edge.source_id == current_id:
                    if edge_types is None or edge.edge_type in edge_types:
                        # Score based on edge weight and distance decay
                        neighbor_score = score * edge.weight * (0.5 ** (dist + 1))
                        neighbors.append((edge.target_id, neighbor_score, edge.edge_type))
            
            # Sort by score and take top N
            neighbors.sort(key=lambda x: x[1], reverse=True)
            neighbors = neighbors[:max_neighbors]
            
            # Add to queue
            for neighbor_id, neighbor_score, edge_type in neighbors:
                if neighbor_id not in visited or neighbor_score > visited[neighbor_id]['score']:
                    new_path = path + [neighbor_id]
                    visited[neighbor_id] = {
                        'distance': dist + 1,
                        'path': new_path,
                        'score': neighbor_score,
                        'edge_type': edge_type.value
                    }
                    queue.append((neighbor_id, dist + 1, new_path, neighbor_score))
        
        return visited
    
    def get_chunks_for_nodes(self, node_ids: List[str], max_chunks_per_doc: int = 3) -> List[Dict[str, Any]]:
        """Get content chunks for given documents"""
        chunks_data = []
        
        for node_id in node_ids:
            if node_id not in self.graph.nodes:
                continue
            
            node = self.graph.nodes[node_id]
            
            # Get chunks for this document
            doc_chunks = [
                self.graph.chunks[chunk_id]
                for chunk_id in node.chunk_ids
                if chunk_id in self.graph.chunks
            ]
            
            # Take top N chunks
            for chunk in doc_chunks[:max_chunks_per_doc]:
                chunks_data.append({
                    'chunk_id': chunk.chunk_id,
                    'document_id': chunk.document_id,
                    'document_title': node.title,
                    'agency': node.agency,
                    'content': chunk.content,
                    'section': chunk.section_title,
                    'source_url': node.source_url
                })
        
        return chunks_data
    
    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        expand_graph: bool = True,
        max_hops: int = 1,
        return_chunks: bool = True,
        strategy: str = "hybrid"
    ) -> RAGResult:
        """
        Main retrieval method combining multiple strategies
        
        Args:
            query: Search query
            top_k: Number of results to return
            expand_graph: Whether to expand via graph traversal
            max_hops: Maximum hops for graph expansion
            return_chunks: Return content chunks instead of just documents
            strategy: "keyword", "graph", or "hybrid"
        
        Returns:
            RAGResult with ranked results
        """
        start_time = time.time()
        
        # Step 1: Keyword search to find seed documents
        keyword_results = self.keyword_search(query, top_k=top_k * 2)
        seed_nodes = [node_id for node_id, score in keyword_results]
        
        if strategy == "keyword":
            # Just use keyword results
            final_nodes = seed_nodes[:top_k]
            search_strategy = "keyword_only"
        
        elif strategy == "graph" and expand_graph:
            # Just use graph expansion (no initial keyword search)
            # Start from index pages
            index_nodes = [
                node_id for node_id, node in self.graph.nodes.items()
                if node.node_type == NodeType.INDEX_PAGE
            ][:5]
            
            expanded = self.expand_via_graph(
                seed_nodes=index_nodes,
                max_hops=max_hops,
                max_neighbors=10,
                edge_types=[EdgeType.HYPERLINK, EdgeType.TOPIC_RELATED]
            )
            
            # Rank by graph score
            final_nodes = sorted(
                expanded.keys(),
                key=lambda x: expanded[x]['score'],
                reverse=True
            )[:top_k]
            search_strategy = "graph_only"
        
        else:  # hybrid (default)
            if expand_graph and seed_nodes:
                # Expand via graph from keyword matches
                expanded = self.expand_via_graph(
                    seed_nodes=seed_nodes[:10],  # Expand from top 10 keyword matches
                    max_hops=max_hops,
                    max_neighbors=5,
                    edge_types=[EdgeType.HYPERLINK, EdgeType.SEMANTIC_SIMILAR, EdgeType.TOPIC_RELATED]
                )
                
                # Combine keyword and graph scores
                combined_scores = {}
                
                # Add keyword scores
                for node_id, kw_score in keyword_results:
                    combined_scores[node_id] = kw_score * 0.7  # Weight keyword matches
                
                # Add/boost graph scores
                for node_id, info in expanded.items():
                    if node_id in combined_scores:
                        combined_scores[node_id] += info['score'] * 0.3
                    else:
                        combined_scores[node_id] = info['score'] * 0.3
                
                # Rank by combined score
                final_nodes = sorted(
                    combined_scores.keys(),
                    key=lambda x: combined_scores[x],
                    reverse=True
                )[:top_k]
                search_strategy = "hybrid_keyword_graph"
            else:
                final_nodes = seed_nodes[:top_k]
                search_strategy = "keyword_only"
        
        # Prepare results
        results = []
        for node_id in final_nodes:
            if node_id not in self.graph.nodes:
                continue
            
            node = self.graph.nodes[node_id]
            
            result = {
                'node_id': node_id,
                'title': node.title,
                'agency': node.agency,
                'type': node.node_type.value,
                'source_url': node.source_url,
                'word_count': node.word_count,
                'topics': node.topics,
                'keywords': node.keywords[:5],
                'pagerank': node.pagerank_score,
                'in_degree': node.in_degree,
                'out_degree': node.out_degree
            }
            
            # Add chunks if requested
            if return_chunks:
                result['chunks'] = self.get_chunks_for_nodes([node_id], max_chunks_per_doc=2)
            
            results.append(result)
        
        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000
        
        return RAGResult(
            query=query,
            results=results,
            total_found=len(results),
            search_strategy=search_strategy,
            execution_time_ms=execution_time_ms,
            expanded_nodes=list(expanded.keys()) if expand_graph and 'expanded' in locals() else []
        )
    
    def get_document_context(self, node_id: str, context_hops: int = 1) -> Dict[str, Any]:
        """
        Get surrounding context for a specific document
        Useful for understanding where a document sits in the knowledge graph
        """
        if node_id not in self.graph.nodes:
            return {}
        
        node = self.graph.nodes[node_id]
        
        # Get direct neighbors
        neighbors = self.expand_via_graph(
            seed_nodes=[node_id],
            max_hops=context_hops,
            max_neighbors=20
        )
        
        # Organize by relationship type
        context = {
            'document': {
                'id': node_id,
                'title': node.title,
                'agency': node.agency,
                'type': node.node_type.value,
                'topics': node.topics
            },
            'related_by_link': [],
            'related_by_topic': [],
            'same_agency': [],
            'parent_child': []
        }
        
        for neighbor_id, info in neighbors.items():
            if neighbor_id == node_id:
                continue
            
            neighbor_node = self.graph.nodes.get(neighbor_id)
            if not neighbor_node:
                continue
            
            neighbor_info = {
                'id': neighbor_id,
                'title': neighbor_node.title,
                'distance': info['distance'],
                'score': info['score']
            }
            
            edge_type = info.get('edge_type', '')
            if 'hyperlink' in edge_type:
                context['related_by_link'].append(neighbor_info)
            elif 'topic' in edge_type:
                context['related_by_topic'].append(neighbor_info)
            elif 'agency' in edge_type:
                context['same_agency'].append(neighbor_info)
            elif 'parent_child' in edge_type:
                context['parent_child'].append(neighbor_info)
        
        return context
    
    def search_by_agency(self, agency: str, query: Optional[str] = None, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search within a specific agency"""
        # Get all documents for agency
        agency_nodes = self.graph.get_by_agency(agency)
        
        if not query:
            # Just return top N documents from agency by importance
            sorted_nodes = sorted(
                agency_nodes,
                key=lambda x: (x.pagerank_score, x.in_degree),
                reverse=True
            )[:top_k]
            
            return [
                {
                    'node_id': node.node_id,
                    'title': node.title,
                    'type': node.node_type.value,
                    'source_url': node.source_url,
                    'pagerank': node.pagerank_score
                }
                for node in sorted_nodes
            ]
        else:
            # Filter by agency, then search
            agency_node_ids = {node.node_id for node in agency_nodes}
            
            # Keyword search
            all_results = self.keyword_search(query, top_k=100)
            
            # Filter to agency
            agency_results = [
                (node_id, score)
                for node_id, score in all_results
                if node_id in agency_node_ids
            ][:top_k]
            
            return [
                {
                    'node_id': node_id,
                    'title': self.graph.nodes[node_id].title,
                    'type': self.graph.nodes[node_id].node_type.value,
                    'source_url': self.graph.nodes[node_id].source_url,
                    'score': score
                }
                for node_id, score in agency_results
            ]


def main():
    """Test RAG retrieval"""
    from src.network.persistence import GraphPersistence
    
    print("Loading knowledge graph...")
    persistence = GraphPersistence(output_dir="src/network/exports")
    graph = persistence.load_pickle("montana_knowledge.pkl", verbose=False)
    
    if not graph:
        print("✗ Could not load graph. Run persistence.py first.")
        return
    
    print(f"Loaded graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges\n")
    
    # Create retriever
    retriever = GraphRAGRetriever(graph)
    
    # Test queries
    queries = [
        "employee benefits and health insurance",
        "hiring and recruitment policies",
        "leave policies and vacation time"
    ]
    
    for query in queries:
        print("=" * 80)
        print(f"Query: {query}")
        print("=" * 80)
        
        # Retrieve
        result = retriever.retrieve(
            query=query,
            top_k=5,
            expand_graph=True,
            max_hops=1,
            return_chunks=False,
            strategy="hybrid"
        )
        
        print(f"\nStrategy: {result.search_strategy}")
        print(f"Found: {result.total_found} documents")
        print(f"Time: {result.execution_time_ms:.2f}ms")
        print(f"Expanded to {len(result.expanded_nodes)} nodes via graph\n")
        
        print("Top Results:")
        for i, doc in enumerate(result.results[:3], 1):
            print(f"\n{i}. {doc['title']}")
            print(f"   Agency: {doc['agency']}")
            print(f"   Type: {doc['type']}")
            print(f"   Topics: {', '.join(doc['topics'][:3])}")
            print(f"   URL: {doc['source_url'][:70]}...")
        
        print("\n")


if __name__ == "__main__":
    main()
