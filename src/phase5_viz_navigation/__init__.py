"""
Phase 5: HTML Navigation Visualization Module

This module provides interactive force-directed network visualizations
for HTML navigation graphs created in Phase 3.

Features:
- Force-directed network layout
- MIME-type based node sizing (domain > HTML > docs)
- Interactive node highlighting on click
- Zoom, pan, drag controls
- Filter by document type
- Click to open URLs

Components:
- html_navigation_viz.py: D3.js force-directed visualization generator

Usage:
    from src.phase5_viz_navigation.html_navigation_viz import HTMLNavigationVisualizer
    viz = HTMLNavigationVisualizer()
    viz.generate_visualization('agriculture')
"""

from pathlib import Path

__version__ = "2.0.0"
__author__ = "Montana State HR Knowledge Network"

# Module paths
PHASE5_DIR = Path(__file__).parent
SRC_DIR = PHASE5_DIR.parent
PROJECT_ROOT = SRC_DIR.parent
