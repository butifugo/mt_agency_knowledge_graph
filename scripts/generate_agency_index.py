#!/usr/bin/env python3
"""
Generate agencies.json index file from available agency data files
This script scans the html/agency-data directory and creates an index
of all available agencies based on .json files present.
"""

import json
from pathlib import Path

def generate_agency_index():
    """Generate the agencies.json index file"""
    # Get the project root
    project_root = Path(__file__).parent.parent
    agency_data_dir = project_root / "html" / "agency-data"
    
    # Find all .json files (excluding agencies.json itself)
    agency_files = sorted([
        f.stem for f in agency_data_dir.glob("*.json")
        if f.name != "agencies.json"
    ])
    
    if not agency_files:
        print("⚠️  No agency JSON files found in html/agency-data/")
        return
    
    # Write the agencies index
    index_file = agency_data_dir / "agencies.json"
    with open(index_file, 'w') as f:
        json.dump(agency_files, f)
    
    print(f"✓ Generated agencies index with {len(agency_files)} agencies:")
    for agency in agency_files:
        print(f"  - {agency}")
    print(f"\n✓ Saved to: {index_file}")

if __name__ == "__main__":
    generate_agency_index()
