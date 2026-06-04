"""
Hierarchy Analyzer
Analyzes and optimizes navigation hierarchies
"""

from typing import Dict, List, Set, Optional
from collections import defaultdict


class HierarchyAnalyzer:
    """Analyzes navigation hierarchy structure"""
    
    def __init__(self, nodes: Dict, edges: List):
        """
        Initialize analyzer
        
        Args:
            nodes: Dictionary of navigation nodes
            edges: List of navigation edges
        """
        self.nodes = nodes
        self.edges = edges
    
    def find_root_nodes(self) -> List[str]:
        """Find all root nodes (nodes with no parents)"""
        root_nodes = []
        
        for node_id, node in self.nodes.items():
            if not node.get('parent') and node.get('type') == 'html_page':
                root_nodes.append(node_id)
        
        return root_nodes
    
    def find_leaf_nodes(self) -> List[str]:
        """Find all leaf nodes (nodes with no children)"""
        leaf_nodes = []
        
        for node_id, node in self.nodes.items():
            if not node.get('children', []):
                leaf_nodes.append(node_id)
        
        return leaf_nodes
    
    def calculate_depth(self) -> Dict[str, int]:
        """Calculate depth of each node from root"""
        depths = {}
        root_nodes = self.find_root_nodes()
        
        # BFS from each root
        from collections import deque
        
        for root_id in root_nodes:
            queue = deque([(root_id, 0)])
            visited = set()
            
            while queue:
                node_id, depth = queue.popleft()
                
                if node_id in visited:
                    continue
                
                visited.add(node_id)
                depths[node_id] = depth
                
                # Add children
                node = self.nodes.get(node_id, {})
                for child_id in node.get('children', []):
                    if child_id not in visited:
                        queue.append((child_id, depth + 1))
        
        return depths
    
    def get_max_depth(self) -> int:
        """Get maximum depth of hierarchy"""
        depths = self.calculate_depth()
        return max(depths.values()) if depths else 0
    
    def get_node_paths(self, node_id: str) -> List[List[str]]:
        """Get all paths from root to this node"""
        paths = []
        
        def backtrack(current_id: str, path: List[str]):
            path.append(current_id)
            
            node = self.nodes.get(current_id, {})
            parent_id = node.get('parent')
            
            if not parent_id:
                # Reached root
                paths.append(list(reversed(path)))
            else:
                backtrack(parent_id, path)
            
            path.pop()
        
        backtrack(node_id, [])
        return paths
    
    def get_breadcrumb(self, node_id: str) -> List[Dict[str, str]]:
        """Get breadcrumb trail for a node"""
        paths = self.get_node_paths(node_id)
        
        if not paths:
            return []
        
        # Use first path
        path = paths[0]
        
        breadcrumb = []
        for nid in path:
            node = self.nodes.get(nid, {})
            breadcrumb.append({
                'id': nid,
                'title': node.get('title', 'Untitled'),
                'url': node.get('url', '')
            })
        
        return breadcrumb
    
    def analyze_structure(self) -> Dict:
        """Comprehensive structure analysis"""
        root_nodes = self.find_root_nodes()
        leaf_nodes = self.find_leaf_nodes()
        depths = self.calculate_depth()
        
        # Count nodes by type
        type_counts = defaultdict(int)
        for node in self.nodes.values():
            node_type = node.get('type', 'unknown')
            type_counts[node_type] += 1
        
        # Calculate branching factor (avg children per node)
        total_children = sum(len(node.get('children', [])) for node in self.nodes.values())
        avg_branching = total_children / len(self.nodes) if self.nodes else 0
        
        return {
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'root_nodes': len(root_nodes),
            'leaf_nodes': len(leaf_nodes),
            'max_depth': self.get_max_depth(),
            'avg_branching_factor': round(avg_branching, 2),
            'type_distribution': dict(type_counts)
        }
