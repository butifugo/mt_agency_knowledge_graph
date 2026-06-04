#!/usr/bin/env python
"""
Build Knowledge Network - Complete Pipeline
Runs all phases to build the Montana State Government Knowledge Network

Usage:
    python src/network/build_network.py                    # Build complete network
    python src/network/build_network.py --quick            # Skip expensive operations
    python src/network/build_network.py --load-existing    # Load and visualize existing graph
"""

import argparse
import time
from pathlib import Path

from src.network.graph_builder import GraphBuilder
from src.network.semantic_layer import SemanticEnhancer
from src.network.persistence import GraphPersistence
from src.network.analyzer import NetworkAnalyzer
from src.network.rag_retriever import GraphRAGRetriever


def build_complete_network(
    knowledge_dir: str = "knowledge",
    output_dir: str = "src/network/exports",
    quick_mode: bool = False,
    verbose: bool = True
):
    """Build complete knowledge network from scratch"""
    
    start_time = time.time()
    
    if verbose:
        print("\n" + "=" * 80)
        print("MONTANA STATE GOVERNMENT KNOWLEDGE NETWORK BUILDER")
        print("=" * 80)
        print()
    
    # Phase 1: Build base graph
    if verbose:
        print("PHASE 1/6: Building Document Graph...")
    
    builder = GraphBuilder(knowledge_dir=knowledge_dir)
    graph = builder.build_graph(verbose=verbose)
    
    phase1_time = time.time() - start_time
    if verbose:
        print(f"✓ Phase 1 complete ({phase1_time:.1f}s)")
        print()
    
    # Phase 2: Semantic enhancement
    if verbose:
        print("PHASE 2/6: Adding Semantic Relationships...")
    
    enhancer = SemanticEnhancer(graph, knowledge_dir=knowledge_dir)
    graph = enhancer.enhance_graph(
        create_chunks_flag=True,
        add_semantic_edges_flag=False if quick_mode else True,  # Skip in quick mode
        add_topic_edges_flag=True,
        similarity_threshold=0.3,
        verbose=verbose
    )
    
    phase2_time = time.time() - start_time - phase1_time
    if verbose:
        print(f"✓ Phase 2 complete ({phase2_time:.1f}s)")
        print()
    
    # Phase 3: Network analysis
    if verbose:
        print("PHASE 3/6: Computing Network Metrics...")
    
    analyzer = NetworkAnalyzer(graph)
    analysis_results = analyzer.analyze_all(verbose=verbose)
    
    phase3_time = time.time() - start_time - phase1_time - phase2_time
    if verbose:
        print(f"✓ Phase 3 complete ({phase3_time:.1f}s)")
        print()
    
    # Phase 4: Persistence
    if verbose:
        print("PHASE 4/6: Saving Network...")
    
    persistence = GraphPersistence(output_dir=output_dir)
    saved_files = persistence.save_all(graph, prefix="montana_knowledge", verbose=verbose)
    
    phase4_time = time.time() - start_time - phase1_time - phase2_time - phase3_time
    if verbose:
        print(f"✓ Phase 4 complete ({phase4_time:.1f}s)")
        print()
    
    # Phase 5: Visualization
    if verbose:
        print("PHASE 5/6: Creating Interactive Visualization...")
        print("  Use 'python src/viz/agency_network_viz.py' to generate visualizations")
    
    viz_path = "html/agency-navigation.html"  # Generated separately by agency_network_viz.py
    
    phase5_time = time.time() - start_time - phase1_time - phase2_time - phase3_time - phase4_time
    if verbose:
        print(f"✓ Phase 5 complete ({phase5_time:.1f}s)")
        print()
    
    # Phase 6: Test RAG retrieval
    if verbose:
        print("PHASE 6/6: Testing RAG Retrieval...")
    
    retriever = GraphRAGRetriever(graph)
    
    # Test query
    test_query = "employee benefits and health insurance"
    result = retriever.retrieve(
        query=test_query,
        top_k=5,
        expand_graph=True,
        max_hops=1,
        return_chunks=False,
        strategy="hybrid"
    )
    
    if verbose:
        print(f"  Test Query: '{test_query}'")
        print(f"  Found: {result.total_found} documents in {result.execution_time_ms:.1f}ms")
        print(f"  Strategy: {result.search_strategy}")
        print(f"  Expanded to {len(result.expanded_nodes)} nodes")
    
    phase6_time = time.time() - start_time - phase1_time - phase2_time - phase3_time - phase4_time - phase5_time
    if verbose:
        print(f"✓ Phase 6 complete ({phase6_time:.1f}s)")
        print()
    
    # Final summary
    total_time = time.time() - start_time
    
    if verbose:
        print("=" * 80)
        print("NETWORK BUILD COMPLETE!")
        print("=" * 80)
        print()
        print(f"Total Time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
        print()
        print("Network Statistics:")
        print(f"  Documents: {graph.total_documents:,}")
        print(f"  Agencies: {graph.total_agencies}")
        print(f"  Relationships: {len(graph.edges):,}")
        print(f"  Content Chunks: {graph.total_chunks:,}")
        print()
        print("Generated Files:")
        print(f"  Graph (JSON): {saved_files['json']}")
        print(f"  Graph (GraphML): {saved_files['graphml']}")
        print(f"  Graph (Pickle): {saved_files['pickle']}")
        print(f"  Chunks (JSON): {saved_files.get('chunks', 'N/A')}")
        print()
        print("Next Steps:")
        print(f"  1. Generate visualization: python src/viz/agency_network_viz.py")
        print(f"  2. Use RAG retrieval in your application")
        print(f"  3. Import GraphML into Gephi/Cytoscape for advanced analysis")
        print()
    
    return graph, analysis_results


def load_and_visualize(output_dir: str = "src/network/exports", verbose: bool = True):
    """Load existing graph and create visualization"""
    
    if verbose:
        print("\nLoading existing knowledge graph...")
    
    persistence = GraphPersistence(output_dir=output_dir)
    graph = persistence.load_pickle("montana_knowledge.pkl", verbose=verbose)
    
    if not graph:
        print("✗ Could not find existing graph. Run without --load-existing to build from scratch.")
        return None
    
    if verbose:
        print(f"Loaded: {len(graph.nodes)} nodes, {len(graph.edges)} edges\n")
        print("Creating visualization...")
        print("  Use 'python src/viz/agency_network_viz.py' to generate interactive visualizations")
    
    viz_path = "html/agency-navigation.html"
    
    if verbose:
        print(f"\n✓ Graph loaded successfully")
        print(f"\nGenerate visualization with: python src/viz/agency_network_viz.py")
    
    return graph


def main():
    parser = argparse.ArgumentParser(
        description="Build Montana State Government Knowledge Network",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: skip expensive semantic similarity calculations"
    )
    
    parser.add_argument(
        "--load-existing",
        action="store_true",
        help="Load existing graph and create visualization (skip building)"
    )
    
    parser.add_argument(
        "--knowledge-dir",
        default="knowledge",
        help="Directory containing markdown knowledge files (default: knowledge)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="src/network/exports",
        help="Directory for output files (default: src/network/exports)"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output"
    )
    
    args = parser.parse_args()
    verbose = not args.quiet
    
    try:
        if args.load_existing:
            load_and_visualize(
                output_dir=args.output_dir,
                verbose=verbose
            )
        else:
            build_complete_network(
                knowledge_dir=args.knowledge_dir,
                output_dir=args.output_dir,
                quick_mode=args.quick,
                verbose=verbose
            )
    except KeyboardInterrupt:
        print("\n\n✗ Build interrupted by user")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
