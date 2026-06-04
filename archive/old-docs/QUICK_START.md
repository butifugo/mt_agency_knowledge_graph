# Quick Start Guide - Refactored Architecture

This guide will help you get started with the refactored Montana State Government Knowledge Network.

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Test the Crawler (Dry Run)

Before actually crawling, test to see what would happen:

```bash
python -m src.phase1_crawl.cli --agency agriculture --dry-run
```

### 3. Crawl a Single Agency

```bash
python -m src.phase1_crawl.cli --agency agriculture
```

### 4. Run Complete Pipeline

```bash
python scripts/run_all.py --agencies agriculture --quick
```

---

## 📖 Available Commands

### Phase 1: Crawling

```bash
# Crawl all agencies
python -m src.phase1_crawl.cli --all

# Crawl specific agency
python -m src.phase1_crawl.cli --agency agriculture

# Crawl multiple agencies
python -m src.phase1_crawl.cli --agency agriculture,commerce,human-resources

# Dry run (preview only)
python -m src.phase1_crawl.cli --all --dry-run

# Update only (skip existing)
python -m src.phase1_crawl.cli --all --update-only
```

### Master Pipeline

```bash
# Complete pipeline (all agencies)
python scripts/run_all.py --all-agencies

# Specific agencies
python scripts/run_all.py --agencies agriculture,commerce

# Skip crawling (use existing data)
python scripts/run_all.py --all-agencies --skip-crawl

# Only run specific phases
python scripts/run_all.py --agencies agriculture --phases 2,4

# Quick mode (skip expensive operations)
python scripts/run_all.py --all-agencies --quick
```

---

## 📁 Where Files Are Saved

| Phase | Output Location | Description |
|-------|----------------|-------------|
| Phase 1 | `knowledge/{agency}/` | Markdown files from crawling |
| Phase 2 | `data/graphs/knowledge/` | Knowledge graph files |
| Phase 3 | `data/graphs/navigation/` | Navigation graph JSON files |
| Phase 4 | `html/knowledge_graph.html` | Knowledge visualization |
| Phase 5 | `html/navigation/{agency}_tree.html` | Navigation trees |
| Phase 6 | `html/interactive_network.html` | Interactive multi-agency viz |

---

## ⚙️ Configuration

Edit `config.yaml` to customize:

```yaml
paths:
  knowledge_dir: "knowledge"      # Change output directory
  
crawling:
  rate_limit_delay: 1.0           # Seconds between requests
  timeout: 30                     # Request timeout
  
visualization:
  knowledge_graph:
    max_nodes: 1000               # Max nodes in visualization
```

---

## 🔍 What's Implemented

### ✅ Fully Implemented
- **Phase 1: Web Crawling**
  - HTML to markdown
  - PDF extraction
  - DOCX extraction
  - CLI interface
  - Dry run mode
  - Update only mode

- **Infrastructure**
  - Shared schemas and utilities
  - Configuration management
  - Master orchestration script

### ⏳ Partially Implemented
- **Orchestration**: Uses existing Phase 2-6 code temporarily

### 🚧 Not Yet Implemented
- **Phase 2: Knowledge Network** (planned)
- **Phase 3: Navigation Network** (planned)
- **Phase 4: Knowledge Visualization** (needs refactoring)
- **Phase 5: Navigation Visualization** (new feature)
- **Phase 6: Interactive Visualization** (new feature)

---

## 🧪 Testing

### Test Phase 1 Crawler

1. **Dry run first:**
   ```bash
   python -m src.phase1_crawl.cli --agency agriculture --dry-run
   ```

2. **Crawl a single agency:**
   ```bash
   python -m src.phase1_crawl.cli --agency agriculture
   ```

3. **Check the output:**
   ```bash
   ls -la knowledge/agriculture/
   ```

4. **Verify markdown files:**
   ```bash
   head -20 knowledge/agriculture/index.md
   ```

### Test Master Pipeline

```bash
# Test with quick mode and single agency
python scripts/run_all.py --agencies agriculture --quick --phases 1
```

---

## 📚 Documentation

- **REFACTORING_PLAN.md** - Complete refactoring plan and architecture
- **IMPLEMENTATION_STATUS.md** - Current implementation status
- **src/phase1_crawl/README.md** - Phase 1 documentation
- **config.yaml** - Configuration reference

---

## 🐛 Troubleshooting

### Import Errors
Make sure you're running from the project root:
```bash
cd "/path/to/hr knowledge"
python -m src.phase1_crawl.cli --help
```

### YAML Not Found
Install PyYAML:
```bash
pip install pyyaml
```

### Rate Limiting Issues
Adjust in config.yaml:
```yaml
crawling:
  rate_limit_delay: 2.0  # Increase delay
```

### Permission Errors
Make sure scripts are executable:
```bash
chmod +x scripts/run_all.py
```

---

## 💡 Tips

1. **Start Small**: Test with one agency before running all
2. **Use Dry Run**: Always preview with `--dry-run` first
3. **Quick Mode**: Use `--quick` for faster testing
4. **Update Only**: Use `--update-only` to skip existing agencies
5. **Check Logs**: Look for error messages in terminal output

---

## 🔄 Migration from Old System

If you have existing data from the old system:

1. **Old crawler** → `src/extract/crawler_1.py`
2. **New crawler** → `src/phase1_crawl/crawler.py`

Both produce compatible output in `knowledge/` directory.

To use new system:
```bash
# Use new Phase 1 crawler
python -m src.phase1_crawl.cli --agency agriculture

# Continue with existing Phase 2 (temporary)
python src/network/3_build_network.py
```

---

## 📞 Next Steps

1. ✅ Test Phase 1 crawler
2. ⏳ Implement Phase 3 (Navigation Network)
3. ⏳ Refactor Phase 2 (Knowledge Network)
4. ⏳ Implement visualizations (Phases 4-6)

---

**Last Updated:** December 8, 2025  
**Version:** 1.0 (Phase 1 Complete)
