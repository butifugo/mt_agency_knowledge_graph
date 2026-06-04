#!/usr/bin/env python3
"""
Refresh script for Montana State Government Knowledge Base
Updates markdown content from Montana state agencies listed in agencies.md

Usage:
    python refresh_2.py              # Crawl all agencies
    python refresh_2.py <folder>     # Crawl specific agency by folder name

Examples:
    python refresh_2.py                    # Crawl all agencies
    python refresh_2.py agriculture        # Crawl only Agriculture department
    python refresh_2.py human-resources    # Crawl only HR
"""

import sys
import re
from pathlib import Path
from datetime import datetime

# Import crawler from same directory
sys.path.insert(0, str(Path(__file__).parent))
from crawler_1 import StateAgencyCrawler


def parse_agencies_file(filepath="agencies.md"):
    """Parse the agencies.md file to extract agency information"""
    agencies = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all table rows with agency data (skip header rows)
        # Pattern: | Agency Name | URL | Folder |
        pattern = r'\|\s*([^|]+?)\s*\|\s*(https?://[^|]+?)\s*\|\s*([^|]+?)\s*\|'
        matches = re.findall(pattern, content)
        
        seen_urls = set()  # Track URLs to avoid duplicates
        
        for match in matches:
            agency_name = match[0].strip()
            url = match[1].strip()
            folder = match[2].strip()
            
            # Skip header rows and separator rows
            if agency_name in ['Agency Name', '---', '']:
                continue
            
            # Skip duplicate URLs (e.g., Auditor and Securities & Insurance share same domain)
            if url in seen_urls:
                print(f"  ℹ Skipping duplicate URL: {agency_name} ({url})")
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
        print("Please create an agencies.md file with the list of agencies to crawl.")
        return []
    except Exception as e:
        print(f"✗ Error parsing {filepath}: {str(e)}")
        return []


def main():
    print("\n" + "=" * 80)
    print("Montana State Government Knowledge Base Refresh")
    print("=" * 80)
    print()
    
    # Check for command-line argument to filter by folder
    target_folder = None
    if len(sys.argv) > 1:
        target_folder = sys.argv[1]
        print(f"🎯 Targeting specific agency folder: {target_folder}\n")
    
    # Parse agencies file
    print("📋 Reading agencies.md...")
    all_agencies = parse_agencies_file("agencies.md")
    
    if not all_agencies:
        print("✗ No agencies found to crawl!")
        return 1
    
    # Filter agencies if target folder specified
    if target_folder:
        agencies = [a for a in all_agencies if a['folder'] == target_folder]
        if not agencies:
            print(f"✗ No agency found with folder '{target_folder}'!")
            print(f"\nAvailable folders:")
            for a in all_agencies:
                print(f"  - {a['folder']} ({a['name']})")
            return 1
        print(f"✓ Found agency: {agencies[0]['name']}\n")
    else:
        agencies = all_agencies
        print(f"✓ Found {len(agencies)} agencies to crawl\n")
    
    # Summary statistics
    total_stats = {
        'agencies_processed': 0,
        'agencies_failed': 0,
        'total_pages': 0,
        'total_pdfs': 0,
        'total_docx': 0,
        'total_files': 0
    }
    
    failed_agencies = []
    
    try:
        # Crawl each agency
        for i, agency in enumerate(agencies, 1):
            print(f"\n[{i}/{len(agencies)}] Processing: {agency['name']}")
            
            try:
                crawler = StateAgencyCrawler(
                    base_url=agency['url'],
                    output_dir="knowledge",
                    agency_name=agency['name'],
                    subfolder=agency['folder']
                )
                
                stats = crawler.crawl()
                
                # Update totals
                total_stats['agencies_processed'] += 1
                total_stats['total_pages'] += stats.get('pages', 0)
                total_stats['total_pdfs'] += stats.get('pdfs', 0)
                total_stats['total_docx'] += stats.get('docx', 0)
                total_stats['total_files'] += stats.get('files', 0)
                
            except Exception as e:
                print(f"\n✗ Error crawling {agency['name']}: {str(e)}")
                total_stats['agencies_failed'] += 1
                failed_agencies.append({
                    'name': agency['name'],
                    'error': str(e)
                })
        
        # Final summary
        print("\n" + "=" * 80)
        print("📊 CRAWL SUMMARY")
        print("=" * 80)
        print(f"Agencies successfully crawled: {total_stats['agencies_processed']}")
        print(f"Agencies failed: {total_stats['agencies_failed']}")
        print(f"Total pages crawled: {total_stats['total_pages']}")
        print(f"Total PDFs extracted: {total_stats['total_pdfs']}")
        print(f"Total DOCX files extracted: {total_stats['total_docx']}")
        print(f"Total files created: {total_stats['total_files']}")
        
        if failed_agencies:
            print("\n⚠️  Failed Agencies:")
            for failed in failed_agencies:
                print(f"  - {failed['name']}: {failed['error']}")
        
        print("\n" + "=" * 80)
        print("✓ Knowledge base refresh complete!")
        print("=" * 80)
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        return 0 if total_stats['agencies_failed'] == 0 else 1
        
    except KeyboardInterrupt:
        print("\n\n✗ Crawl interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
