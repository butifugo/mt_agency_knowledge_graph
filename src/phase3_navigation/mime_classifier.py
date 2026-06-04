"""
MIME Type Classifier
Classifies documents by MIME type and creates hierarchical structure
"""

from typing import Dict, List, Set
from collections import defaultdict


class MimeClassifier:
    """Classifies and organizes documents by MIME type"""
    
    # MIME type categories
    HTML_TYPES = ['text/html']
    PDF_TYPES = ['application/pdf']
    DOCX_TYPES = [
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword'
    ]
    
    def __init__(self, nodes: Dict):
        """
        Initialize classifier
        
        Args:
            nodes: Dictionary of navigation nodes
        """
        self.nodes = nodes
    
    def classify_by_mime_type(self) -> Dict[str, List[str]]:
        """
        Classify all nodes by MIME type
        
        Returns:
            Dictionary mapping MIME types to node IDs
        """
        classified = defaultdict(list)
        
        for node_id, node in self.nodes.items():
            mime_type = node.get('mime_type', 'unknown')
            classified[mime_type].append(node_id)
        
        return dict(classified)
    
    def get_html_pages(self) -> List[str]:
        """Get all HTML page node IDs"""
        html_nodes = []
        
        for node_id, node in self.nodes.items():
            if node.get('type') == 'html_page':
                html_nodes.append(node_id)
        
        return html_nodes
    
    def get_documents(self) -> Dict[str, List[str]]:
        """
        Get all document nodes (non-HTML)
        
        Returns:
            Dictionary with 'pdf' and 'docx' lists
        """
        documents = {
            'pdf': [],
            'docx': []
        }
        
        for node_id, node in self.nodes.items():
            node_type = node.get('type')
            
            if node_type == 'pdf_document':
                documents['pdf'].append(node_id)
            elif node_type == 'docx_document':
                documents['docx'].append(node_id)
        
        return documents
    
    def get_navigation_backbone(self) -> List[str]:
        """
        Get the navigation backbone (HTML pages only)
        
        Returns:
            List of HTML page node IDs in hierarchical order
        """
        html_pages = self.get_html_pages()
        
        # Sort by level (depth in hierarchy)
        sorted_pages = sorted(
            html_pages,
            key=lambda nid: self.nodes[nid].get('level', 999)
        )
        
        return sorted_pages
    
    def get_document_parents(self) -> Dict[str, List[str]]:
        """
        Get parent HTML pages for all documents
        
        Returns:
            Dictionary mapping HTML page IDs to their document children
        """
        doc_parents = defaultdict(list)
        
        for node_id, node in self.nodes.items():
            if node.get('type') in ['pdf_document', 'docx_document']:
                parent_id = node.get('parent')
                if parent_id:
                    doc_parents[parent_id].append(node_id)
        
        return dict(doc_parents)
    
    def create_mime_hierarchy(self) -> Dict:
        """
        Create hierarchical structure organized by MIME type
        
        Returns:
            Hierarchical structure with HTML pages as primary nodes
        """
        hierarchy = {
            'html_pages': [],
            'documents': {
                'pdf': [],
                'docx': []
            }
        }
        
        # Get navigation backbone (HTML pages)
        html_pages = self.get_navigation_backbone()
        doc_parents = self.get_document_parents()
        
        for page_id in html_pages:
            page_node = self.nodes[page_id]
            
            page_data = {
                'id': page_id,
                'url': page_node.get('url'),
                'title': page_node.get('title'),
                'level': page_node.get('level'),
                'children': {
                    'html': [],
                    'pdf': [],
                    'docx': []
                }
            }
            
            # Add child HTML pages
            for child_id in page_node.get('children', []):
                child_node = self.nodes.get(child_id)
                if not child_node:
                    continue
                
                child_type = child_node.get('type')
                
                if child_type == 'html_page':
                    page_data['children']['html'].append(child_id)
                elif child_type == 'pdf_document':
                    page_data['children']['pdf'].append(child_id)
                elif child_type == 'docx_document':
                    page_data['children']['docx'].append(child_id)
            
            hierarchy['html_pages'].append(page_data)
        
        # Add orphaned documents (no HTML parent)
        for node_id, node in self.nodes.items():
            if node.get('type') == 'pdf_document' and not node.get('parent'):
                hierarchy['documents']['pdf'].append(node_id)
            elif node.get('type') == 'docx_document' and not node.get('parent'):
                hierarchy['documents']['docx'].append(node_id)
        
        return hierarchy
    
    def get_statistics(self) -> Dict:
        """Get MIME type statistics"""
        classified = self.classify_by_mime_type()
        documents = self.get_documents()
        
        return {
            'total_nodes': len(self.nodes),
            'html_pages': len(self.get_html_pages()),
            'pdf_documents': len(documents['pdf']),
            'docx_documents': len(documents['docx']),
            'mime_types': {
                mime_type: len(nodes)
                for mime_type, nodes in classified.items()
            }
        }
