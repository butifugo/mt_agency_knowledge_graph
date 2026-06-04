"""
Phase 1 CLI - Web Crawling Interface
Command-line interface for crawling state agency websites
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.shared.config import Config
from src.phase1_crawl.crawler import WebCrawler


def parse_agencies_file(filepath: str) -> List[Dict[str, str]]:
    """Parse agencies.md file to extract agency information"""
    agencies = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all table rows with agency data
        pattern = r'\|\s*([^|]+?)\s*\|\s*(https?://[^|]+?)\s*\|\s*([^|]+?)\s*\|'
        matches = re.findall(pattern, content)
        
        seen_urls = set()
        
        for match in matches:
            agency_name = match[0].strip()
            url = match[1].strip()
            folder = match[2].strip()
            
            # Skip header rows and separator rows
            if agency_name in ['Agency Name', '---', '']:
                continue
            
            # Skip duplicate URLs
            if url in seen_urls:
                continue
            
            seen_urls.add(url)
            agencies.append({
                'name': agency_name,
                'url': url,
                'folder': folder
            })
        
        return agencies
        
    except FileNotFoundError:
        print(f"✗ Error: {filepath} not found!")
        return []
    except Exception as e:
        print(f"✗ Error parsing {filepath}: {str(e)}")
        return []


def crawl_agency(agency: Dict[str, str], config: Config, update_only: bool = False) -> Dict[str, Any]:
    """Crawl a single agency"""
    output_dir = config.knowledge_dir / agency['folder']
    
    # Skip if update_only and directory exists
    if update_only and output_dir.exists():
        print(f"ℹ Skipping {agency['name']} (already exists)")
        return {'skipped': True}
    
    # Create crawler
    crawler = WebCrawler(
        base_url=agency['url'],
        output_dir=str(output_dir),
        agency_name=agency['name'],
        rate_limit=config.get('crawling.rate_limit_delay', 1.0),
        timeout=config.get('crawling.timeout', 30),
        user_agent=config.get('crawling.user_agent')
    )
    
    # Run crawl
    return crawler.crawl()


def main():
    parser = argparse.ArgumentParser(
        description='Phase 1: Crawl Montana state agency websites',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Crawl all agencies
  python -m src.phase1_crawl.cli --all
  
  # Crawl specific agency
  python -m src.phase1_crawl.cli --agency agriculture
  
  # Crawl multiple agencies
  python -m src.phase1_crawl.cli --agency agriculture,commerce,human-resources
  
  # Dry run (show what would be crawled)
  python -m src.phase1_crawl.cli --all --dry-run
  
  # Update only (skip existing)
  python -m src.phase1_crawl.cli --all --update-only
        """
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Crawl all agencies from agencies.md'
    )
    
    parser.add_argument(
        '--agency',
        type=str,
        help='Crawl specific agency(ies) by folder name (comma-separated)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be crawled without actually crawling'
    )
    
    parser.add_argument(
        '--update-only',
        action='store_true',
        help='Skip agencies that already have data'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.all and not args.agency:
        parser.error('Must specify either --all or --agency')
    
    # Load configuration
    config = Config(args.config if Path(args.config).exists() else None)
    
    # Parse agencies file
    print(f"\n📋 Reading {config.agencies_file}...")
    all_agencies = parse_agencies_file(str(config.agencies_file))
    
    if not all_agencies:
        print("✗ No agencies found!")
        return 1
    
    # Filter agencies if specific ones requested
    if args.agency:
        target_folders = [f.strip() for f in args.agency.split(',')]
        agencies = [a for a in all_agencies if a['folder'] in target_folders]
        
        if not agencies:
            print(f"✗ No agencies found with folder(s): {', '.join(target_folders)}")
            print(f"\nAvailable folders:")
            for a in all_agencies:
                print(f"  - {a['folder']} ({a['name']})")
            return 1
    else:
        agencies = all_agencies
    
    print(f"Found {len(agencies)} agenc{'y' if len(agencies) == 1 else 'ies'} to crawl\n")
    
    # Dry run mode
    if args.dry_run:
        print("DRY RUN MODE - No actual crawling will occur\n")
        for agency in agencies:
            output_dir = config.knowledge_dir / agency['folder']
            status = "EXISTS" if output_dir.exists() else "NEW"
            print(f"[{status}] {agency['name']}")
            print(f"  URL: {agency['url']}")
            print(f"  Output: {output_dir}")
            print()
        return 0
    
    # Crawl agencies
    results = []
    for i, agency in enumerate(agencies, 1):
        print(f"\n[{i}/{len(agencies)}] Processing: {agency['name']}")
        print("-" * 80)
        
        result = crawl_agency(agency, config, args.update_only)
        results.append({**agency, **result})
    
    # Print summary
    print(f"\n{'='*80}")
    print("CRAWL SUMMARY")
    print(f"{'='*80}\n")
    
    total_html = sum(r.get('html_pages', 0) for r in results)
    total_pdf = sum(r.get('pdf_documents', 0) for r in results)
    total_docx = sum(r.get('docx_documents', 0) for r in results)
    total_errors = sum(r.get('errors', 0) for r in results)
    skipped = sum(1 for r in results if r.get('skipped', False))
    
    print(f"Agencies processed: {len(agencies)}")
    if skipped:
        print(f"Agencies skipped: {skipped}")
    print(f"HTML pages: {total_html}")
    print(f"PDF documents: {total_pdf}")
    print(f"DOCX documents: {total_docx}")
    if total_errors:
        print(f"Errors: {total_errors}")
    
    print(f"\n{'='*80}\n")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
