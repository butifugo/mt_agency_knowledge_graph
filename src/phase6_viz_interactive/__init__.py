"""
Phase 6: Interactive Multi-Agency Dashboard

This module provides a unified interactive dashboard combining knowledge graphs
and navigation trees with advanced filtering, search, and export capabilities.

Features:
- Multi-agency selection interface
- Dual-view layout (knowledge graph + navigation tree)
- Network complexity controls (node limits, edge filters)
- Search and filter functionality
- Synchronized view interactions
- Export capabilities (PNG, SVG, JSON)

Components:
- dashboard_viz.py: Unified dashboard generator
- cli.py: Command-line interface

Usage:
    python -m src.phase6_viz_interactive.cli
    python -m src.phase6_viz_interactive.cli --agencies agriculture,commerce
"""

from pathlib import Path

__version__ = "1.0.0"
__author__ = "Montana State HR Knowledge Network"

# Module paths
PHASE6_DIR = Path(__file__).parent
SRC_DIR = PHASE6_DIR.parent
PROJECT_ROOT = SRC_DIR.parent
