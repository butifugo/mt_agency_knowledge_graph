#!/bin/zsh
# Activate the virtual environment
source "$(dirname "$0")/.venv/bin/activate"
echo "✓ Virtual environment activated"
echo "You can now use: python, pip"
echo ""
echo "To run scripts:"
echo "  python refresh.py"
echo "  python refresh.py human-resources"
echo "  python visualizations/visualize_network.py knowledge/hr_original"
echo "  python check_accessibility.py https://hr.mt.gov/"
