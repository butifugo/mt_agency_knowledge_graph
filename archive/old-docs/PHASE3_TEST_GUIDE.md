# Quick Test Guide - Phase 3

Test the complete Phase 3 Navigation Network implementation.

## Prerequisites

```bash
# Ensure PyYAML is installed
pip install pyyaml
```

## Quick Tests

### 1. Test CLI Help
```bash
python -m src.phase3_navigation.cli --help
```
**Expected:** Help text with all commands and examples

### 2. Build Navigation for One Agency
```bash
python -m src.phase3_navigation.cli --build --agency agriculture
```
**Expected:**
- Processes ~1477 markdown files
- Creates ~1476 nodes
- Saves to `data/graphs/navigation/agriculture_navigation.json`

### 3. Analyze Navigation Structure
```bash
python -m src.phase3_navigation.cli --analyze --agency agriculture
```
**Expected:**
- Total nodes, edges count
- Root/leaf node counts
- Maximum depth
- Type distribution
- MIME statistics

### 4. Build All Agencies
```bash
python -m src.phase3_navigation.cli --build-all --quiet
```
**Expected:**
- Processes all agencies in `knowledge/` directory
- Creates JSON file for each
- Shows summary at end

### 5. Export to GraphML
```bash
python -m src.phase3_navigation.cli --export --agency agriculture --format graphml
```
**Expected:**
- Creates `agriculture_navigation.graphml`
- Valid XML format

### 6. Via Master Pipeline
```bash
# Run Phase 3 only
python scripts/run_all.py --agencies agriculture --phases 3

# Run Phases 1 and 3
python scripts/run_all.py --agencies agriculture --phases 1,3
```

## Verify Output

### Check Navigation JSON
```bash
# View file size
ls -lh data/graphs/navigation/agriculture_navigation.json

# Preview structure
head -50 data/graphs/navigation/agriculture_navigation.json

# Count nodes
python -c "import json; data=json.load(open('data/graphs/navigation/agriculture_navigation.json')); print(f'Nodes: {len(data[\"nodes\"])}')"

# Count edges
python -c "import json; data=json.load(open('data/graphs/navigation/agriculture_navigation.json')); print(f'Edges: {len(data[\"edges\"])}')"
```

## Expected Results

### Agriculture Agency
- **Files processed:** ~1477 markdown files
- **Nodes created:** ~1476
  - HTML pages: ~357
  - PDF documents: ~1082
  - DOCX documents: ~37
- **Edges created:** ~39
- **Max depth:** 1-2 levels
- **Output size:** ~600KB JSON

### All Agencies
- **Total agencies:** 9
- **Processing time:** ~30 seconds
- **Total navigation graphs:** 9 JSON files

## Troubleshooting

### Error: "Module not found 'yaml'"
```bash
pip install pyyaml
```

### Error: "Agency directory not found"
```bash
# Check available agencies
ls knowledge/
```

### Error: "Navigation graph not found" (for --analyze)
```bash
# Build first
python -m src.phase3_navigation.cli --build --agency agriculture
```

## Success Indicators

✅ CLI help displays correctly  
✅ Build completes without errors  
✅ JSON file created in `data/graphs/navigation/`  
✅ Analysis shows reasonable statistics  
✅ Export creates valid GraphML  
✅ Master pipeline integration works  

## Next Steps

Once Phase 3 is validated:
1. Review `NEXT_STEPS_IMPLEMENTATION.md` for priorities
2. Start Phase 2 refactor or Phase 5 implementation
3. Test combined Phase 1 + Phase 3 pipeline
