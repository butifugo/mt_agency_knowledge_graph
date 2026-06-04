#!/usr/bin/env python3
"""
Master Orchestration Script
Runs complete pipeline: crawl → knowledge → navigation → visualizations

Usage:
    python scripts/run_all.py --all-agencies
    python scripts/run_all.py --agencies agriculture,commerce
    python scripts/run_all.py --all-agencies --skip-crawl
    python scripts/run_all.py --phases 2,3,4,5,6
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.shared.config import Config


def run_phase1_crawl(agencies: str, all_agencies: bool, config: Config, update_only: bool = False):
    """Run Phase 1: Web Crawling"""
    print("\n" + "="*80)
    print("PHASE 1: WEB CRAWLING & CONTENT EXTRACTION")
    print("="*80 + "\n")
    
    import subprocess
    
    cmd = [sys.executable, "-m", "src.phase1_crawl.cli"]
    
    if all_agencies:
        cmd.append("--all")
    elif agencies:
        cmd.extend(["--agency", agencies])
    
    if update_only:
        cmd.append("--update-only")
    
    result = subprocess.run(cmd, cwd=str(project_root))
    return result.returncode == 0


def run_phase2_knowledge(agencies: str, all_agencies: bool, quick_mode: bool, config: Config):
    """Run Phase 2: Knowledge Network Building"""
    print("\n" + "="*80)
    print("PHASE 2: KNOWLEDGE NETWORK BUILDING")
    print("="*80 + "\n")
    
    import subprocess
    
    # Build knowledge graphs
    cmd = [sys.executable, "-m", "src.phase2_knowledge.cli"]
    
    if all_agencies:
        cmd.append("--build-all")
    elif agencies:
        # Split agencies and run for each
        for agency in agencies.split(','):
            agency = agency.strip()
            agency_cmd = cmd + ["--build", "--agency", agency]
            
            # Add enhancement if not in quick mode
            if not quick_mode:
                agency_cmd.append("--enhance")
            
            result = subprocess.run(agency_cmd, cwd=str(project_root))
            if result.returncode != 0:
                return False
        return True
    
    # Add enhancement if not in quick mode
    if not quick_mode and all_agencies:
        # For all agencies, enhance separately
        print("\nEnhancing knowledge graphs with semantic relationships...")
        # This would need a separate enhancement step for all agencies
        # For now, users can run --enhance separately
    
    result = subprocess.run(cmd, cwd=str(project_root))
    return result.returncode == 0


def run_phase3_navigation(agencies: str, all_agencies: bool, config: Config):
    """Run Phase 3: Navigation Network Building"""
    print("\n" + "="*80)
    print("PHASE 3: NAVIGATION NETWORK BUILDING")
    print("="*80 + "\n")
    
    import subprocess
    
    cmd = [sys.executable, "-m", "src.phase3_navigation.cli"]
    
    if all_agencies:
        cmd.append("--build-all")
    elif agencies:
        # Split agencies and run for each
        for agency in agencies.split(','):
            agency_cmd = cmd + ["--build", "--agency", agency.strip()]
            result = subprocess.run(agency_cmd, cwd=str(project_root))
            if result.returncode != 0:
                return False
        return True
    
    result = subprocess.run(cmd, cwd=str(project_root))
    return result.returncode == 0


def run_phase4_viz_knowledge(config: Config):
    """Run Phase 4: Knowledge Graph Visualization"""
    print("\n" + "="*80)
    print("PHASE 4: KNOWLEDGE GRAPH VISUALIZATION")
    print("="*80 + "\n")
    
    import subprocess
    
    cmd = [sys.executable, "-m", "src.phase4_viz_knowledge.cli", "--all"]
    
    result = subprocess.run(cmd, cwd=str(project_root))
    return result.returncode == 0


def run_phase5_viz_navigation(agencies: str, all_agencies: bool, config: Config):
    """Run Phase 5: Navigation Tree Visualization"""
    print("\n" + "="*80)
    print("PHASE 5: NAVIGATION TREE VISUALIZATION")
    print("="*80 + "\n")
    
    import subprocess
    
    cmd = [sys.executable, "-m", "src.phase5_viz_navigation.cli", "--layout", "both"]
    
    if all_agencies:
        cmd.append("--all")
    elif agencies:
        cmd.extend(["--agency", agencies])
    
    result = subprocess.run(cmd, cwd=str(project_root))
    return result.returncode == 0


def run_phase6_viz_interactive(config: Config):
    """Run Phase 6: Interactive Multi-Agency Visualization"""
    print("\n" + "="*80)
    print("PHASE 6: INTERACTIVE MULTI-AGENCY VISUALIZATION")
    print("="*80 + "\n")
    
    import subprocess
    
    cmd = [sys.executable, "-m", "src.phase6_viz_interactive.cli"]
    
    result = subprocess.run(cmd, cwd=str(project_root))
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(
        description='Run complete Montana Knowledge Network pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Complete pipeline (all agencies, all phases)
  python scripts/run_all.py --all-agencies

  # Specific agencies
  python scripts/run_all.py --agencies agriculture,commerce,human-resources

  # Skip crawling (use existing data)
  python scripts/run_all.py --all-agencies --skip-crawl

  # Only run phases 2-6 (skip crawling)
  python scripts/run_all.py --all-agencies --phases 2,3,4,5,6

  # Quick mode (skip expensive semantic operations)
  python scripts/run_all.py --all-agencies --quick

  # Only generate visualizations (phases 4-6)
  python scripts/run_all.py --agencies agriculture --phases 4,5,6
        """
    )
    
    parser.add_argument(
        '--all-agencies',
        action='store_true',
        help='Process all agencies from agencies.md'
    )
    
    parser.add_argument(
        '--agencies',
        type=str,
        help='Comma-separated list of agency folder names'
    )
    
    parser.add_argument(
        '--skip-crawl',
        action='store_true',
        help='Skip Phase 1 (crawling)'
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick mode (skip expensive operations like semantic similarity)'
    )
    
    parser.add_argument(
        '--phases',
        type=str,
        default='1,2,3,4,5,6',
        help='Comma-separated list of phases to run (default: all)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--update-only',
        action='store_true',
        help='For Phase 1: skip agencies that already exist'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.all_agencies and not args.agencies:
        parser.error('Must specify either --all-agencies or --agencies')
    
    # Load configuration
    config = Config(args.config if Path(args.config).exists() else None)
    
    # Parse phases to run
    if args.skip_crawl:
        phases = [2, 3, 4, 5, 6]
    else:
        phases = [int(p.strip()) for p in args.phases.split(',')]
    
    print("\n" + "="*80)
    print("MONTANA STATE GOVERNMENT KNOWLEDGE NETWORK")
    print("Master Pipeline Orchestrator")
    print("="*80)
    print(f"\nAgencies: {args.agencies if args.agencies else 'ALL'}")
    print(f"Phases: {', '.join(map(str, phases))}")
    print(f"Quick mode: {'Yes' if args.quick else 'No'}")
    print()
    
    # Run phases
    success = True
    
    if 1 in phases:
        success = run_phase1_crawl(
            args.agencies or "",
            args.all_agencies,
            config,
            args.update_only
        ) and success
    
    if 2 in phases:
        success = run_phase2_knowledge(
            args.agencies or "",
            args.all_agencies,
            args.quick,
            config
        ) and success
    
    if 3 in phases:
        success = run_phase3_navigation(
            args.agencies or "",
            args.all_agencies,
            config
        ) and success
    
    if 4 in phases:
        success = run_phase4_viz_knowledge(config) and success
    
    if 5 in phases:
        success = run_phase5_viz_navigation(
            args.agencies or "",
            args.all_agencies,
            config
        ) and success
    
    if 6 in phases:
        success = run_phase6_viz_interactive(config) and success
    
    # Final summary
    print("\n" + "="*80)
    print("PIPELINE COMPLETE" if success else "PIPELINE COMPLETED WITH ERRORS")
    print("="*80 + "\n")
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
