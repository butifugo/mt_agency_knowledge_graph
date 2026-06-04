# Montana State Agency Presentation Generator - Complete Guide

## 🎯 Overview

This system automatically generates professional 30-minute presentations for each Montana state agency, describing the services they provide to Montana citizens. Each presentation is created in both **Markdown** (for editing) and **PowerPoint** (for delivery) formats with Montana's official government color scheme.

## 📊 What Gets Generated

For each agency, the system creates:

1. **Markdown Source File** (`{agency}_presentation.md`)
   - Editable text format
   - 15-20 slides of content
   - Service categorization by type

2. **PowerPoint Presentation** (`{agency}_presentation.pptx`)
   - Professional slides with Montana government branding
   - Neutral blues and greys color scheme
   - Ready for 30-minute delivery

## 🎨 Montana Government Color Scheme

All presentations use the official color palette:

| Color Name | Hex Code | Usage |
|------------|----------|-------|
| Primary Blue | `#003F87` | Titles and main headers |
| Secondary Blue | `#4A90E2` | Subtitles and accents |
| Dark Gray | `#333333` | Body text |
| Medium Gray | `#666666` | Secondary text |
| Light Gray | `#E5E5E5` | Backgrounds |
| White | `#FFFFFF` | Slide backgrounds |
| Accent Blue | `#0066CC` | Highlights |

## 📁 Output Structure

```
presentations/
├── README.md
├── administration/
│   ├── administration_presentation.md
│   └── administration_presentation.pptx
├── agriculture/
│   ├── agriculture_presentation.md
│   └── agriculture_presentation.pptx
├── human-resources/
│   ├── human-resources_presentation.md
│   └── human-resources_presentation.pptx
└── [... all 36 agencies ...]
```

## 🚀 Quick Start

### Prerequisites

1. **Knowledge network must be built first:**
   ```bash
   python build_network.py
   ```

2. **Install PowerPoint library:**
   ```bash
   pip install python-pptx
   ```

### Generate All Presentations

```bash
python visualizations/presentation_generator.py
```

This will:
- Process all 36 Montana state agencies
- Generate markdown and PowerPoint for each
- Takes approximately 5-10 minutes
- Creates ~72 files (2 per agency)

### Generate Specific Agency

```bash
# By agency folder name
python visualizations/presentation_generator.py --agency human-resources
python visualizations/presentation_generator.py --agency commerce
python visualizations/presentation_generator.py --agency agriculture

# Find agency folder names in agencies.md
```

### Generate Markdown Only

```bash
# Skip PowerPoint generation (faster)
python visualizations/presentation_generator.py --md-only

# For specific agency
python visualizations/presentation_generator.py --agency commerce --md-only
```

## 📋 Presentation Structure

Each presentation includes these slides:

### 1. Title Slide
- Agency name
- "Services for Montana Citizens"
- State of Montana branding
- Current date

### 2. Agenda
- Overview of presentation topics
- 8 main sections

### 3. Mission & Overview
- Agency purpose and role
- Key responsibilities
- Mission statement (extracted from agency content)

### 4-9. Service Categories
Services are automatically categorized into:

- **Citizen Services** - Individual residents and families
- **Business Services** - Commercial entities and employers
- **Government Services** - Inter-agency and governmental
- **Programs & Benefits** - Support programs and assistance
- **Regulations & Compliance** - Requirements and rules
- **Resources & Information** - Guides, forms, documents

Each category includes:
- Service titles
- Brief descriptions
- Links to more information

### 10. Key Service Areas
- Most frequently referenced topics
- Statistical overview of service areas

### 11. How to Access Services
- Online (24/7 website access)
- In Person (office visits)
- By Phone (contact center)
- By Mail (applications and documents)

### 12. Contact Information
- Official website URL
- General contact methods
- Stay connected options

### 13. Thank You / Q&A
- Closing slide with call to action

## 🔧 How It Works

### 1. Content Analysis
The system uses the knowledge network to:
- Search agency documents for service-related content
- Extract mission statements and overviews
- Identify key service areas
- Categorize services by audience and type

### 2. Markdown Generation
Creates structured presentation content:
- Organized into logical slides
- Separated by `---` delimiters
- Markdown formatting for emphasis
- 30-minute speaking time (15-20 slides)

### 3. PowerPoint Conversion
Converts markdown to PowerPoint:
- Applies Montana color scheme
- Formats text hierarchically
- Sizes appropriately for readability
- Creates professional layouts

## ✏️ Customizing Presentations

### Edit Markdown Files

1. **Open the markdown file:**
   ```bash
   # Example
   open presentations/commerce/commerce_presentation.md
   ```

2. **Edit content:**
   - Modify service descriptions
   - Add/remove slides (separate with `---`)
   - Update contact information
   - Refine mission statements

3. **Regenerate PowerPoint:**
   ```bash
   python visualizations/presentation_generator.py --agency commerce
   ```

### Add Custom Slides

Insert anywhere in the markdown file between `---` delimiters:

```markdown
---

## Your Custom Slide Title

### Subtitle (optional)

- Bullet point 1
- Bullet point 2
- **Bold text** for emphasis
- More details

---
```

### Modify Color Scheme

Edit `visualizations/presentation_generator.py`:

```python
class PowerPointConverter:
    MONTANA_COLORS = {
        'primary_blue': '#003F87',    # Change here
        'secondary_blue': '#4A90E2',  # Change here
        # ... etc
    }
```

## 🔄 Updating Presentations

When agency content changes:

### Step 1: Refresh Knowledge Base
```bash
# Crawl agency websites for new content
python refresh.py
```

### Step 2: Rebuild Knowledge Network
```bash
# Rebuild the graph with updated content
python build_network.py
```

### Step 3: Regenerate Presentations
```bash
# All agencies
python visualizations/presentation_generator.py

# Or specific agencies
python visualizations/presentation_generator.py --agency commerce
python visualizations/presentation_generator.py --agency agriculture
```

## 📊 Use Cases

### Public Presentations
- Community meetings
- Town halls
- Public forums
- Citizen education sessions

### Internal Use
- New employee orientations
- Cross-agency briefings
- Leadership updates
- Strategic planning

### Government Operations
- Legislative testimony
- Budget justifications
- Program reviews
- Annual reports

### External Relations
- Grant applications
- Partnership presentations
- Stakeholder briefings
- Media events

## 🎓 Advanced Usage

### Custom Graph Path
```bash
python visualizations/presentation_generator.py \
  --graph-path /path/to/custom/graph.pkl
```

### Custom Agencies File
```bash
python visualizations/presentation_generator.py \
  --agencies-file custom_agencies.md
```

### Batch Processing Script

Create `generate_all.sh`:
```bash
#!/bin/bash
# Generate presentations for all agencies

agencies=(
  "administration"
  "agriculture"
  "commerce"
  "human-resources"
  # ... add all agencies
)

for agency in "${agencies[@]}"; do
  echo "Generating $agency..."
  python visualizations/presentation_generator.py --agency "$agency"
done

echo "All presentations generated!"
```

## 🐛 Troubleshooting

### No Content Generated

**Problem:** Empty or minimal slides

**Solutions:**
1. Verify knowledge network is built:
   ```bash
   ls -lh network/exports/montana_knowledge.pkl
   ```

2. Check agency has crawled content:
   ```bash
   ls knowledge/human-resources/
   ```

3. Re-crawl agency:
   ```bash
   # Edit agencies.md to include only that agency
   python refresh.py
   ```

### PowerPoint Not Created

**Problem:** Only markdown file generated

**Solutions:**
1. Install python-pptx:
   ```bash
   pip install python-pptx
   ```

2. Check for errors in terminal output

3. Use markdown-only mode if PowerPoint not needed:
   ```bash
   python visualizations/presentation_generator.py --md-only
   ```

### Services Missing or Incomplete

**Problem:** Expected services not appearing

**Solutions:**
1. Ensure content is crawled:
   ```bash
   python refresh.py
   ```

2. Rebuild network:
   ```bash
   python build_network.py
   ```

3. Check RAG retrieval manually:
   ```python
   from network.persistence import GraphPersistence
   from network.rag_retriever import GraphRAGRetriever
   
   persistence = GraphPersistence()
   graph = persistence.load_pickle("network/exports/montana_knowledge.pkl")
   retriever = GraphRAGRetriever(graph)
   
   results = retriever.search_by_agency("human-resources", "services")
   for r in results[:5]:
       print(r['title'])
   ```

### Presentation Too Long/Short

**Problem:** Timing doesn't match 30 minutes

**Solutions:**
1. Edit markdown to add/remove slides
2. Adjust content density
3. Modify service limits in code:
   ```python
   # In visualizations/presentation_generator.py
   services, keywords = analyzer.extract_services(agency['folder'])
   # Increase/decrease top_k parameter
   ```

## 📈 Quality Tips

### For Better Results

1. **Ensure Current Content**
   - Regularly refresh knowledge base
   - Keep agencies.md up to date
   - Verify URLs are active

2. **Review Before Delivery**
   - Check markdown for accuracy
   - Verify contact information
   - Update agency-specific details

3. **Customize for Audience**
   - Edit examples for context
   - Add local statistics
   - Include recent initiatives

4. **Test Timing**
   - Practice delivery
   - Adjust slide count
   - Allow time for questions

## 🔍 Technical Details

### Content Sources

Presentations are generated from:
- Agency website pages (HTML)
- PDF documents
- DOCX files
- All content in `knowledge/{agency}/` folders

### Service Categorization

Uses keyword matching and semantic analysis:
- **Citizen:** citizen, resident, public, individual, family
- **Business:** business, commercial, industry, employer, license
- **Programs:** program, benefit, assistance, grant, fund
- **Regulations:** regulation, compliance, requirement, rule
- **Resources:** resource, information, guide, form, document

### RAG-Based Extraction

Uses knowledge graph for intelligent retrieval:
1. Semantic search for relevant content
2. Graph traversal to find related documents
3. Topic-based categorization
4. Importance scoring (PageRank)

## 📞 Support Resources

- **Main README:** `/README.md` - Project overview
- **Network Guide:** `/network/README.md` - Knowledge graph details
- **Presentations README:** `/presentations/README.md` - Folder overview
- **Agencies List:** `/agencies.md` - All agency information

## 🎯 Best Practices

### DO:
- ✅ Rebuild network before generating presentations
- ✅ Review markdown before converting to PowerPoint
- ✅ Customize content for specific audiences
- ✅ Update regularly as agency services change
- ✅ Test presentation timing before delivery

### DON'T:
- ❌ Edit PowerPoint directly (edit markdown instead)
- ❌ Skip rebuilding network after content changes
- ❌ Use outdated graph files
- ❌ Forget to verify contact information
- ❌ Assume all services are captured (review manually)

## 📝 Example Workflow

### Complete Presentation Creation

```bash
# 1. Ensure environment is ready
pip install -r requirements.txt

# 2. Crawl agency content (if needed)
python refresh.py

# 3. Build knowledge network
python build_network.py

# 4. Generate presentations
python visualizations/presentation_generator.py

# 5. Review and customize
# Edit presentations/human-resources/human-resources_presentation.md

# 6. Regenerate PowerPoint
python visualizations/presentation_generator.py --agency human-resources

# 7. Open and verify
open presentations/human-resources/human-resources_presentation.pptx
```

## 🏆 Success Metrics

A successful presentation includes:
- ✅ 15-20 slides for 30-minute delivery
- ✅ Clear agency mission and overview
- ✅ 6-8 categorized service areas
- ✅ Current contact information
- ✅ Professional Montana government branding
- ✅ Accurate, up-to-date content
- ✅ Both markdown and PowerPoint formats

---

**Created by Montana State Government Knowledge System**
*Automated Presentation Generation for Citizen Service Delivery*

**Version:** 1.0  
**Last Updated:** December 2025  
**Python Required:** 3.9+  
**Dependencies:** python-pptx, networkx, all knowledge system requirements
