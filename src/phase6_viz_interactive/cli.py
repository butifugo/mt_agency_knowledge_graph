"""
Command-line interface for Phase 6: Interactive Multi-Agency Dashboard

Usage:
    python -m src.phase6_viz_interactive.cli
    python -m src.phase6_viz_interactive.cli --agencies agriculture,commerce
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List

from .dashboard_viz import DashboardGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Generate interactive multi-agency dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate dashboard with all available agencies
  python -m src.phase6_viz_interactive.cli
  
  # Generate dashboard with specific agencies
  python -m src.phase6_viz_interactive.cli --agencies agriculture,commerce,human-resources
  
  # Use custom config
  python -m src.phase6_viz_interactive.cli --config config.yaml
        """
    )
    
    parser.add_argument(
        '--agencies',
        type=str,
        help='Comma-separated list of agency names (default: all available)'
    )
    
    parser.add_argument(
        '--config',
        type=Path,
        default=None,
        help='Path to config.yaml (optional)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress informational output'
    )
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = DashboardGenerator(config_path=args.config)
    
    # Get agencies
    if args.agencies:
        agencies = [a.strip() for a in args.agencies.split(',')]
    else:
        agencies = None  # Will use all available
    
    # Get available agencies
    available = generator.get_available_agencies()
    
    if not available:
        logger.error("No agencies found with both knowledge and navigation graphs")
        logger.error(f"Knowledge graphs: {generator.knowledge_dir}")
        logger.error(f"Navigation graphs: {generator.navigation_dir}")
        return 1
    
    if not args.quiet:
        logger.info(f"Found {len(available)} agencies with complete data")
        logger.info(f"Agencies: {', '.join(available)}")
    
    # Validate specified agencies
    if agencies:
        invalid = [a for a in agencies if a not in available]
        if invalid:
            logger.error(f"Invalid agencies (missing data): {', '.join(invalid)}")
            logger.error(f"Available agencies: {', '.join(available)}")
            return 1
        
        if not args.quiet:
            logger.info(f"Using {len(agencies)} specified agencies")
    else:
        agencies = available
        if not args.quiet:
            logger.info(f"Using all {len(agencies)} available agencies")
    
    # Generate dashboard
    try:
        if not args.quiet:
            logger.info("Generating interactive dashboard...")
        
        output_file = generator.generate_dashboard(agencies)
        
        if not args.quiet:
            logger.info(f"\n{'='*60}")
            logger.info(f"✓ Dashboard generated: {output_file}")
            logger.info(f"  Agencies: {len(agencies)}")
            logger.info(f"  Output: {Path(output_file).stat().st_size / 1024:.1f} KB")
            logger.info(f"{'='*60}\n")
            logger.info(f"🌐 Start the web server to view the dashboard:")
            logger.info(f"  python serve_dashboard.py")
            logger.info(f"\n  Then open: http://localhost:8000/interactive-dashboard.html")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error generating dashboard: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
