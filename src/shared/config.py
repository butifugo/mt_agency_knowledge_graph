"""
Configuration Management
Loads and provides access to configuration settings
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Configuration manager with defaults"""
    
    DEFAULT_CONFIG = {
        'paths': {
            'knowledge_dir': 'knowledge',
            'graphs_dir': 'data/graphs',
            'html_dir': 'html',
            'agencies_file': 'agencies.md'
        },
        'crawling': {
            'rate_limit_delay': 1.0,
            'timeout': 30,
            'max_retries': 3,
            'allowed_extensions': ['.html', '.htm', '.pdf', '.docx'],
            'user_agent': 'Mozilla/5.0 (Montana Knowledge Crawler)'
        },
        'knowledge': {
            'semantic_similarity': {
                'enabled': True,
                'threshold': 0.3,
                'method': 'tfidf'
            },
            'topic_modeling': {
                'enabled': True,
                'num_topics': 20
            },
            'rag': {
                'chunk_size': 512,
                'chunk_overlap': 50
            }
        },
        'navigation': {
            'max_depth': 10,
            'mime_types': {
                'html': ['text/html'],
                'pdf': ['application/pdf'],
                'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document']
            }
        },
        'visualization': {
            'knowledge_graph': {
                'max_nodes': 1000,
                'layout': 'force-directed'
            },
            'navigation_tree': {
                'layout': 'tree'
            },
            'interactive': {
                'default_agencies': ['agriculture', 'commerce', 'human-resources'],
                'max_nodes': 500,
                'enable_filters': True
            }
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': 'pipeline.log'
        },
        'performance': {
            'parallel_processing': True,
            'max_workers': 4,
            'cache_enabled': True,
            'cache_dir': '.cache'
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            config_file: Path to YAML config file (optional)
        """
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_file and Path(config_file).exists():
            self.load_from_file(config_file)
    
    def load_from_file(self, config_file: str):
        """Load configuration from YAML file"""
        with open(config_file, 'r') as f:
            user_config = yaml.safe_load(f)
        
        # Deep merge user config with defaults
        self._deep_merge(self.config, user_config)
    
    def _deep_merge(self, base: Dict, update: Dict):
        """Recursively merge update into base"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated path
        
        Args:
            path: Dot-separated path (e.g., 'paths.knowledge_dir')
            default: Default value if path not found
            
        Returns:
            Configuration value
        """
        keys = path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, path: str, value: Any):
        """Set configuration value by dot-separated path"""
        keys = path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    @property
    def knowledge_dir(self) -> Path:
        """Get knowledge directory path"""
        return Path(self.get('paths.knowledge_dir'))
    
    @property
    def graphs_dir(self) -> Path:
        """Get graphs directory path"""
        return Path(self.get('paths.graphs_dir'))
    
    @property
    def html_dir(self) -> Path:
        """Get HTML output directory path"""
        return Path(self.get('paths.html_dir'))
    
    @property
    def agencies_file(self) -> Path:
        """Get agencies file path"""
        return Path(self.get('paths.agencies_file'))
