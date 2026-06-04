# Navigation Network Feature

## Overview

The crawler now automatically creates a navigation network for each agency during the crawling process. This network captures the link structure and relationships between all documents (HTML pages, PDFs, and DOCX files) discovered during the crawl.

## How It Works

### During Crawling

1. **Node Creation**: Every document (HTML page, PDF, or DOCX) is added as a node in the network with:
   - Title
   - Document type (html_page, pdf_document, docx_document)
   - File path (relative to agency folder)
   - Source URL
   - Crawl timestamp

2. **Edge Creation**: Every hyperlink discovered is recorded as an edge with:
   - Source URL (the page containing the link)
   - Target URL (the linked document)
   - Link text (the anchor text)
   - Context (surrounding text, up to 200 characters)
   - Edge type (hyperlink, pdf_link, docx_link)

### Network Storage

After crawling completes, a `navigation_network.json` file is saved in each agency's knowledge folder with:

```json
{
  "agency": "Agency Name",
  "base_url": "https://example.mt.gov/",
  "created": "2025-12-06 HH:MM:SS",
  "statistics": {
    "total_nodes": 150,
    "total_edges": 420,
    "html_pages": 120,
    "pdf_documents": 25,
    "docx_documents": 5
  },
  "nodes": {
    "https://example.mt.gov/page1": {
      "title": "Page Title",
      "type": "html_page",
      "file_path": "page1.md",
      "url": "https://example.mt.gov/page1",
      "crawled": "2025-12-06 HH:MM:SS"
    }
  },
  "edges": [
    {
      "source": "https://example.mt.gov/page1",
      "target": "https://example.mt.gov/page2",
      "link_text": "Click here",
      "context": "Visit our services page. Click here to learn more about...",
      "type": "hyperlink"
    }
  ]
}
```

## Benefits

1. **Navigation Understanding**: Understand how documents link to each other
2. **Important Pages**: Identify central/hub pages based on link counts
3. **Document Relationships**: See how PDFs and DOCX files relate to HTML pages
4. **RAG Enhancement**: Use the network to improve retrieval by following relevant links
5. **Knowledge Graph**: Can be integrated with the semantic network in `network/`

## Usage

The navigation network is created automatically when you run:

```bash
# Single agency
python crawler.py "Agency Name" https://agency.mt.gov/ agency-folder

# All agencies via refresh
python refresh.py
```

## File Location

Each agency's navigation network is stored at:
```
knowledge/<agency-folder>/navigation_network.json
```

For example:
- `knowledge/human-resources/navigation_network.json`
- `knowledge/administration/navigation_network.json`

## Integration with Existing Features

All existing crawler features are preserved:
- HTML to Markdown conversion
- PDF text extraction
- DOCX document processing
- Metadata in frontmatter
- Content cleaning
- Polite crawling with delays

The navigation network is an additive feature that enhances the knowledge base without changing existing functionality.

## Future Enhancements

The navigation network can be used to:
- Build interactive visualizations of agency website structures
- Calculate PageRank or centrality metrics for important pages
- Improve RAG by retrieving linked documents
- Detect broken or outdated links
- Merge with the semantic knowledge graph in `network/`
