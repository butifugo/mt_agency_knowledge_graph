"""
Network Analyzer - Phase 6
Computes graph metrics and provides analytical insights
"""

import networkx as nx
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter

from src.network.schema import KnowledgeGraph, NodeType, EdgeType


class NetworkAnalyzer:
    """Analyzes the knowledge graph and computes metrics"""
    
    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph
        self.nx_graph: Optional[nx.DiGraph] = None
    
    def to_networkx(self) -> nx.DiGraph:
        """Convert KnowledgeGraph to NetworkX DiGraph"""
        if self.nx_graph is not None:
            return self.nx_graph
        
        G = nx.DiGraph()
        
        # Add nodes
        for node_id, node in self.graph.nodes.items():
            G.add_node(node_id, **{
                'title': node.title,
                'agency': node.agency,
                'type': node.node_type.value,
                'word_count': node.word_count
            })
        
        # Add edges
        for edge in self.graph.edges:
            G.add_edge(
                edge.source_id,
                edge.target_id,
                weight=edge.weight,
                type=edge.edge_type.value
            )
        
        self.nx_graph = G
        return G
    
    def compute_pagerank(self, alpha: float = 0.85) -> Dict[str, float]:
        """Compute PageRank scores for all nodes"""
        G = self.to_networkx()
        pagerank = nx.pagerank(G, alpha=alpha)
        
        # Update graph nodes with scores
        for node_id, score in pagerank.items():
            if node_id in self.graph.nodes:
                self.graph.nodes[node_id].pagerank_score = score
        
        return pagerank
    
    def compute_betweenness_centrality(self) -> Dict[str, float]:
        """Compute betweenness centrality for all nodes"""
        G = self.to_networkx()
        betweenness = nx.betweenness_centrality(G)
        
        # Update graph nodes with scores
        for node_id, score in betweenness.items():
            if node_id in self.graph.nodes:
                self.graph.nodes[node_id].betweenness_centrality = score
        
        return betweenness
    
    def find_communities(self) -> Dict[str, int]:
        """Find communities using Louvain algorithm"""
        # Convert to undirected for community detection
        G = self.to_networkx().to_undirected()
        
        try:
            import community as community_louvain
            communities = community_louvain.best_partition(G)
            return communities
        except ImportError:
            print("  Note: Install python-louvain for community detection")
            return {}
    
    def find_hubs_and_authorities(self) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Compute HITS algorithm (hubs and authorities)"""
        G = self.to_networkx()
        hubs, authorities = nx.hits(G)
        return hubs, authorities
    
    def get_most_important_documents(self, top_n: int = 20) -> List[Dict]:
        """Get most important documents by multiple metrics"""
        # Ensure we have computed metrics
        if not any(node.pagerank_score > 0 for node in self.graph.nodes.values()):
            self.compute_pagerank()
        
        # Score documents by combined metrics
        scored_docs = []
        for node_id, node in self.graph.nodes.items():
            score = (
                node.pagerank_score * 0.4 +
                node.betweenness_centrality * 0.3 +
                (node.in_degree / 100) * 0.2 +
                (node.out_degree / 100) * 0.1
            )
            scored_docs.append({
                'node_id': node_id,
                'title': node.title,
                'agency': node.agency,
                'type': node.node_type.value,
                'score': score,
                'pagerank': node.pagerank_score,
                'betweenness': node.betweenness_centrality,
                'in_degree': node.in_degree,
                'out_degree': node.out_degree
            })
        
        # Sort by score
        scored_docs.sort(key=lambda x: x['score'], reverse=True)
        return scored_docs[:top_n]
    
    def get_agency_statistics(self) -> Dict[str, Dict]:
        """Get statistics per agency"""
        agency_stats = {}
        
        for agency, node_ids in self.graph.agency_index.items():
            nodes = [self.graph.nodes[nid] for nid in node_ids if nid in self.graph.nodes]
            
            # Separate agency node from document nodes
            doc_nodes = [n for n in nodes if n.node_type != NodeType.AGENCY_ROOT]
            agency_node = next((n for n in nodes if n.node_type == NodeType.AGENCY_ROOT), None)
            
            # Count document types
            type_counts = Counter(node.node_type.value for node in doc_nodes)
            
            # Calculate metrics
            total_words = sum(node.word_count for node in doc_nodes)
            total_chunks = sum(node.chunk_count for node in doc_nodes)
            avg_pagerank = sum(node.pagerank_score for node in doc_nodes) / len(doc_nodes) if doc_nodes else 0
            
            # Topic distribution
            all_topics = []
            for node in doc_nodes:
                all_topics.extend(node.topics)
            topic_counts = Counter(all_topics)
            
            # Agency node metrics
            agency_pagerank = agency_node.pagerank_score if agency_node else 0.0
            agency_connections = (agency_node.in_degree + agency_node.out_degree) if agency_node else 0
            
            agency_stats[agency] = {
                'total_documents': len(doc_nodes),
                'total_words': total_words,
                'total_chunks': total_chunks,
                'avg_pagerank': avg_pagerank,
                'document_types': dict(type_counts),
                'top_topics': dict(topic_counts.most_common(5)),
                'agency_pagerank': agency_pagerank,
                'agency_connections': agency_connections,
                'has_agency_node': agency_node is not None
            }
        
        return agency_stats
    
    def find_shortest_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """Find shortest path between two documents"""
        G = self.to_networkx()
        
        try:
            path = nx.shortest_path(G, source_id, target_id)
            return path
        except nx.NetworkXNoPath:
            return None
    
    def get_connected_components(self) -> List[List[str]]:
        """Find weakly connected components"""
        G = self.to_networkx()
        components = list(nx.weakly_connected_components(G))
        return [list(comp) for comp in components]
    
    def analyze_edge_types(self) -> Dict[str, Dict]:
        """Analyze distribution and characteristics of edge types"""
        edge_type_stats = defaultdict(lambda: {
            'count': 0,
            'avg_weight': 0,
            'avg_confidence': 0,
            'weights': []
        })
        
        for edge in self.graph.edges:
            stats = edge_type_stats[edge.edge_type.value]
            stats['count'] += 1
            stats['weights'].append(edge.weight)
            stats['avg_confidence'] += edge.confidence
        
        # Calculate averages
        for edge_type, stats in edge_type_stats.items():
            if stats['count'] > 0:
                stats['avg_weight'] = sum(stats['weights']) / stats['count']
                stats['avg_confidence'] /= stats['count']
                del stats['weights']  # Remove raw data
        
        return dict(edge_type_stats)
    
    def get_network_summary(self) -> Dict:
        """Get comprehensive network summary"""
        G = self.to_networkx()
        
        summary = {
            'nodes': len(G.nodes()),
            'edges': len(G.edges()),
            'agencies': len(self.graph.agency_index),
            'density': nx.density(G),
            'avg_clustering': nx.average_clustering(G.to_undirected()),
            'num_components': nx.number_weakly_connected_components(G),
            'largest_component_size': len(max(nx.weakly_connected_components(G), key=len)),
            'node_types': {},
            'edge_types': {}
        }
        
        # Node type distribution
        for node_type, node_ids in self.graph.type_index.items():
            summary['node_types'][node_type.value] = len(node_ids)
        
        # Edge type distribution
        edge_types = Counter(edge.edge_type.value for edge in self.graph.edges)
        summary['edge_types'] = dict(edge_types)
        
        return summary
    
    def analyze_all(self, verbose: bool = True) -> Dict:
        """Run all analyses and return comprehensive results"""
        if verbose:
            print("=" * 80)
            print("Network Analysis - Phase 6")
            print("=" * 80)
            print()
        
        results = {}
        
        # Compute PageRank
        if verbose:
            print("Computing PageRank scores...")
        results['pagerank'] = self.compute_pagerank()
        if verbose:
            top_pr = sorted(results['pagerank'].items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"  Top 5 by PageRank:")
            for node_id, score in top_pr:
                print(f"    {self.graph.nodes[node_id].title[:60]}: {score:.4f}")
            print()
        
        # Compute Betweenness Centrality
        if verbose:
            print("Computing betweenness centrality...")
        results['betweenness'] = self.compute_betweenness_centrality()
        if verbose:
            top_bc = sorted(results['betweenness'].items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"  Top 5 by Betweenness:")
            for node_id, score in top_bc:
                if score > 0:
                    print(f"    {self.graph.nodes[node_id].title[:60]}: {score:.4f}")
            print()
        
        # Get important documents
        if verbose:
            print("Identifying most important documents...")
        results['important_docs'] = self.get_most_important_documents(top_n=20)
        if verbose:
            print(f"  Top 10 Most Important Documents:")
            for i, doc in enumerate(results['important_docs'][:10], 1):
                print(f"    {i}. {doc['title'][:55]} ({doc['agency']})")
            print()
        
        # Agency statistics
        if verbose:
            print("Computing agency statistics...")
        results['agency_stats'] = self.get_agency_statistics()
        if verbose:
            print(f"  Agency Statistics:")
            for agency, stats in sorted(results['agency_stats'].items(), 
                                       key=lambda x: x[1]['total_documents'], reverse=True):
                print(f"    {agency}: {stats['total_documents']} docs, "
                      f"{stats['total_words']:,} words, "
                      f"avg PageRank: {stats['avg_pagerank']:.4f}")
            print()
        
        # Edge analysis
        if verbose:
            print("Analyzing edge types...")
        results['edge_analysis'] = self.analyze_edge_types()
        if verbose:
            print(f"  Edge Type Distribution:")
            for edge_type, stats in sorted(results['edge_analysis'].items(),
                                          key=lambda x: x[1]['count'], reverse=True):
                print(f"    {edge_type}: {stats['count']} edges, "
                      f"avg weight: {stats['avg_weight']:.3f}")
            print()
        
        # Network summary
        if verbose:
            print("Computing network summary...")
        results['summary'] = self.get_network_summary()
        if verbose:
            print(f"  Network Metrics:")
            print(f"    Nodes: {results['summary']['nodes']}")
            print(f"    Edges: {results['summary']['edges']}")
            print(f"    Density: {results['summary']['density']:.6f}")
            print(f"    Avg Clustering: {results['summary']['avg_clustering']:.4f}")
            print(f"    Connected Components: {results['summary']['num_components']}")
            print()
        
        # Update graph metrics
        self.graph.graph_metrics = results['summary']
        self.graph.update_statistics()
        
        if verbose:
            print("=" * 80)
            print("Network Analysis Complete - Phase 6")
            print("=" * 80)
            print()
        
        return results


def main():
    """Run network analysis"""
    from src.network.persistence import GraphPersistence
    
    print("Loading knowledge graph...")
    persistence = GraphPersistence(output_dir="src/network/exports")
    graph = persistence.load_pickle("montana_knowledge.pkl", verbose=False)
    
    if not graph:
        print("✗ Could not load graph.")
        return
    
    print(f"Loaded graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges\n")
    
    # Analyze
    analyzer = NetworkAnalyzer(graph)
    results = analyzer.analyze_all(verbose=True)
    
    # Save updated graph with metrics
    print("Saving graph with computed metrics...")
    persistence.save_pickle(graph, "montana_knowledge_analyzed.pkl", verbose=True)
    
    print("\n✓ Analysis complete!")


if __name__ == "__main__":
    main()
