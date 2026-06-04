"""
HTML Navigation CLI
Command-line interface for extracting and visualizing HTML navigation structure
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.phase3_navigation.html_navigation_extractor import HTMLNavigationExtractor
from src.phase5_viz_navigation.html_navigation_viz import HTMLNavigationVisualizer


def main():
    parser = argparse.ArgumentParser(
        description='Extract and visualize HTML navigation structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract and visualize for one agency
  python -m src.phase3_navigation.html_nav_cli --agency agriculture
  
  # Extract only
  python -m src.phase3_navigation.html_nav_cli --agency agriculture --extract-only
  
  # Visualize from existing data
  python -m src.phase3_navigation.html_nav_cli --agency agriculture --viz-only
  
  # Process all agencies
  python -m src.phase3_navigation.html_nav_cli --all
        """
    )
    
    parser.add_argument(
        '--agency',
        type=str,
        help='Agency name to process (e.g., agriculture, human-resources)'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all agencies found in knowledge directory'
    )
    
    parser.add_argument(
        '--extract-only',
        action='store_true',
        help='Only extract navigation data, do not visualize'
    )
    
    parser.add_argument(
        '--viz-only',
        action='store_true',
        help='Only visualize existing navigation data'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress verbose output'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.agency and not args.all:
        parser.error('Either --agency or --all must be specified')
    
    if args.agency and args.all:
        parser.error('Cannot specify both --agency and --all')
    
    # Get list of agencies to process
    if args.all:
        knowledge_dir = Path('knowledge')
        if not knowledge_dir.exists():
            print(f"✗ Knowledge directory not found: {knowledge_dir}")
            return 1
        
        agencies = [d.name for d in knowledge_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        
        if not agencies:
            print("✗ No agencies found in knowledge directory")
            return 1
        
        print(f"Found {len(agencies)} agencies: {', '.join(agencies)}\\n")
    else:
        agencies = [args.agency]
    
    # Initialize tools
    extractor = HTMLNavigationExtractor()
    visualizer = HTMLNavigationVisualizer()
    
    # Process each agency
    for agency in agencies:
        print(f"{'='*80}")
        print(f"Processing: {agency}")
        print(f"{'='*80}\\n")
        
        try:
            # Extract navigation data
            if not args.viz_only:
                extractor.extract_navigation(agency, verbose=not args.quiet)
            
            # Generate visualization
            if not args.extract_only:
                output_path = visualizer.generate_visualization(agency)
                
                if not args.quiet:
                    print(f"\\n✓ Visualization ready: {output_path}")
                    print(f"  Open in browser: file://{output_path.absolute()}\\n")
        
        except Exception as e:
            print(f"✗ Error processing {agency}: {e}\\n")
            continue
    
    print(f"{'='*80}")
    print("Processing complete!")
    print(f"{'='*80}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
