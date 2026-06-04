# 📝 Quick Reference Card

## Montana State Government Knowledge Network - Refactored

---

## 🚀 Most Common Commands

### Phase 1: Crawl a Single Agency
```bash
python -m src.phase1_crawl.cli --agency agriculture
```

### Run Complete Pipeline
```bash
python scripts/run_all.py --agencies agriculture --quick
```

### Dry Run (Preview Only)
```bash
python -m src.phase1_crawl.cli --agency agriculture --dry-run
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `config.yaml` | Configuration settings |
| `agencies.md` | List of agencies to crawl |
| `src/phase1_crawl/cli.py` | Phase 1 command-line interface |
| `scripts/run_all.py` | Master pipeline orchestrator |

---

## 📚 Documentation

| Document | Content |
|----------|---------|
| `QUICK_START.md` | Getting started guide |
| `REFACTORING_PLAN.md` | Complete architecture plan |
| `IMPLEMENTATION_STATUS.md` | Current progress |
| `IMPLEMENTATION_SUMMARY.md` | What's been implemented |

---

## 🎯 Phase 1 CLI Options

```bash
python -m src.phase1_crawl.cli [OPTIONS]

--all              # Crawl all agencies
--agency NAME      # Crawl specific agency(ies)
--dry-run          # Preview without crawling
--update-only      # Skip existing agencies
--config FILE      # Custom config file
```

---

## 🎯 Master Pipeline Options

```bash
python scripts/run_all.py [OPTIONS]

--all-agencies     # Process all agencies
--agencies LIST    # Specific agencies (comma-separated)
--skip-crawl       # Skip Phase 1
--quick            # Quick mode (skip expensive ops)
--phases LIST      # Run specific phases (comma-separated)
--update-only      # Skip existing data
--config FILE      # Custom config file
```

---

## 📊 Output Locations

| Phase | Output |
|-------|--------|
| Phase 1 | `knowledge/{agency}/*.md` |
| Phase 2 | `data/graphs/knowledge/*.pkl` |
| Phase 3 | `data/graphs/navigation/*.json` |
| Phase 4 | `html/knowledge_graph.html` |
| Phase 5 | `html/navigation/{agency}_tree.html` |
| Phase 6 | `html/interactive_network.html` |

---

## ⚡ Quick Examples

### Example 1: Test Crawler
```bash
# Dry run first
python -m src.phase1_crawl.cli --agency agriculture --dry-run

# Actually crawl
python -m src.phase1_crawl.cli --agency agriculture

# Check output
ls knowledge/agriculture/
```

### Example 2: Multiple Agencies
```bash
python -m src.phase1_crawl.cli --agency agriculture,commerce,human-resources
```

### Example 3: Complete Pipeline
```bash
# Quick mode with specific agencies
python scripts/run_all.py --agencies agriculture,commerce --quick

# All agencies, skip crawling
python scripts/run_all.py --all-agencies --skip-crawl
```

### Example 4: Update Existing Data
```bash
# Only crawl new agencies
python -m src.phase1_crawl.cli --all --update-only
```

---

## 🔧 Configuration Quick Edit

Edit `config.yaml`:

```yaml
# Adjust crawling speed
crawling:
  rate_limit_delay: 2.0  # Slower (more polite)

# Change output directory
paths:
  knowledge_dir: "data/knowledge"

# Visualization settings
visualization:
  knowledge_graph:
    max_nodes: 500  # Fewer nodes
```

---

## ✅ Implementation Status

| Component | Status |
|-----------|--------|
| Infrastructure | ✅ Complete |
| Phase 1: Crawling | ✅ Complete |
| Phase 2: Knowledge | ⏳ Planned |
| Phase 3: Navigation | ⏳ Planned |
| Phase 4: Viz Knowledge | ⏳ Planned |
| Phase 5: Viz Navigation | ⏳ Planned |
| Phase 6: Viz Interactive | ⏳ Planned |
| Orchestration | ✅ Complete |
| Documentation | ✅ Complete |

---

## 🐛 Troubleshooting

### Import Errors
```bash
# Run from project root
cd "/path/to/hr knowledge"
python -m src.phase1_crawl.cli --help
```

### Module Not Found
```bash
# Install dependencies
pip install -r requirements.txt
```

### Permission Errors
```bash
# Make scripts executable
chmod +x scripts/run_all.py
```

### Configuration Not Found
```bash
# Use default config or specify
python -m src.phase1_crawl.cli --agency agriculture --config config.yaml
```

---

## 📞 Need More Help?

- **Quick Start**: See `QUICK_START.md`
- **Full Plan**: See `REFACTORING_PLAN.md`
- **Current Status**: See `IMPLEMENTATION_STATUS.md`
- **What's Done**: See `IMPLEMENTATION_SUMMARY.md`

---

## 🎓 Key Concepts

### Phases Overview
1. **Phase 1** - Crawl websites → markdown
2. **Phase 2** - Build knowledge graph
3. **Phase 3** - Build navigation hierarchy
4. **Phase 4** - Visualize knowledge
5. **Phase 5** - Visualize navigation
6. **Phase 6** - Interactive multi-agency viz

### Data Flow
```
agencies.md → Phase 1 → knowledge/*.md
knowledge/*.md → Phase 2 → graphs/knowledge/*.pkl
knowledge/*.md → Phase 3 → graphs/navigation/*.json
graphs/* → Phase 4-6 → html/*.html
```

---

**Last Updated:** December 8, 2025  
**Version:** 1.0
