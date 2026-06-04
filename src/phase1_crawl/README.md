# Phase 1: Web Crawling & Content Extraction

Extracts and converts website content to markdown format.

## Features

- ✅ HTML to markdown conversion
- ✅ PDF text extraction
- ✅ DOCX text extraction
- ✅ Rate limiting and error handling
- ✅ CLI for single or multiple agencies
- ✅ Dry run mode
- ✅ Update only mode (skip existing)

## Usage

### Crawl all agencies
```bash
python -m src.phase1_crawl.cli --all
```

### Crawl specific agency
```bash
python -m src.phase1_crawl.cli --agency agriculture
```

### Crawl multiple agencies
```bash
python -m src.phase1_crawl.cli --agency agriculture,commerce,human-resources
```

### Dry run (preview without crawling)
```bash
python -m src.phase1_crawl.cli --all --dry-run
```

### Update only (skip existing directories)
```bash
python -m src.phase1_crawl.cli --all --update-only
```

## Output

Creates markdown files in `knowledge/{agency}/` with:
- Source URL metadata
- Document title
- Crawl timestamp
- Document type (html, pdf, docx)
- Converted content

## Components

- `crawler.py` - Main crawler engine
- `extractors/html_extractor.py` - HTML to markdown converter
- `extractors/pdf_extractor.py` - PDF text extractor
- `extractors/docx_extractor.py` - DOCX text extractor
- `cli.py` - Command-line interface

## Configuration

Settings in `config.yaml`:
```yaml
crawling:
  rate_limit_delay: 1.0  # Seconds between requests
  timeout: 30  # Request timeout
  max_retries: 3
  user_agent: "Mozilla/5.0 (Montana Knowledge Crawler)"
```
