# Presentations Directory

Automatically generated PowerPoint presentations for Montana State Government agencies, describing the services they provide to Montana citizens, businesses, and other government entities.

## 📋 Overview

This directory contains professional 30-minute presentations for each Montana state agency. Presentations are automatically generated from the knowledge base content, organized by service type, and formatted with Montana government branding.

### Key Features
- **Automated Generation** - Created from actual agency website content
- **Service Categorization** - Organized by Citizen, Business, Government services
- **Professional Design** - Montana state government color scheme
- **Dual Format** - Both PowerPoint (.pptx) and Markdown (.md)
- **Ready to Present** - 30-minute format with 15-20 slides

## 📁 Directory Structure

```
presentations/
├── README.md                          # This file (documentation)
│
├── administration/                    # Department of Administration
│   ├── administration_presentation.md   # Markdown source
│   └── administration_presentation.pptx # PowerPoint presentation
│
├── agriculture/                       # Department of Agriculture
│   ├── agriculture_presentation.md
│   └── agriculture_presentation.pptx
│
├── commerce/                          # Department of Commerce
│   ├── commerce_presentation.md
│   └── commerce_presentation.pptx
│
├── corrections/                       # Department of Corrections
│   ├── corrections_presentation.md
│   └── corrections_presentation.pptx
│
├── environmental-quality/             # Department of Environmental Quality
│   ├── environmental-quality_presentation.md
│   └── environmental-quality_presentation.pptx
│
├── human-resources/                   # State Human Resources
│   ├── human-resources_presentation.md
│   └── human-resources_presentation.pptx
│
├── labor-industry/                    # Department of Labor & Industry
│   ├── labor-industry_presentation.md
│   └── labor-industry_presentation.pptx
│
└── [Additional agencies]/             # More agencies as generated
```

## 🎨 Presentation Design

### Montana Government Color Palette

All PowerPoint presentations use the official Montana state government colors:

- **Primary Blue**: `#003F87` - Titles and headers
- **Secondary Blue**: `#4A90E2` - Subtitles and accents
- **Dark Gray**: `#333333` - Body text
- **Medium Gray**: `#666666` - Secondary text
- **Light Gray**: `#E5E5E5` - Backgrounds and borders
- **White**: `#FFFFFF` - Main slide backgrounds
- **Accent Blue**: `#0066CC` - Links and highlights

### Typography
- **Title Font**: Calibri Bold, 44pt
- **Subtitle Font**: Calibri Regular, 28pt
- **Body Font**: Calibri Regular, 18pt
- **Bullet Points**: Calibri Regular, 16pt

### Layout
- Clean, modern design
- Consistent header/footer placement
- Montana state branding elements
- Professional government aesthetic

## 📊 Presentation Content

### Standard Slide Structure (15-20 slides)

1. **Title Slide**
   - Agency name
   - Presentation title
   - Date and presenter info

2. **Agenda Slide**
   - Overview of topics to be covered
   - Presentation flow

3. **Mission & Overview**
   - Agency mission statement
   - Core responsibilities
   - Service scope

4. **Citizen Services**
   - Services for individual Montana residents
   - Eligibility and access methods
   - Key programs

5. **Business Services**
   - Services for Montana businesses
   - Licensing and permits
   - Compliance requirements

6. **Government Services**
   - Inter-agency services
   - Local government support
   - Coordination efforts

7. **Programs & Benefits**
   - Support programs
   - Grants and funding
   - Benefits administration

8. **Regulations & Compliance**
   - Regulatory requirements
   - Standards and guidelines
   - Enforcement activities

9. **Resources & Information**
   - Forms and applications
   - Guides and handbooks
   - Educational materials

10. **Key Service Areas**
    - Most frequently accessed services
    - Priority programs

11. **Service Delivery Methods**
    - Online services
    - In-person locations
    - Phone support
    - Mail services

12. **Contact Information**
    - Website URL
    - Phone numbers
    - Office locations
    - Hours of operation

13. **Thank You / Q&A**
    - Summary
    - Contact for questions
    - Next steps

## 🚀 Generating Presentations

### Prerequisites

1. **Knowledge Base** - Crawled agency content
   ```bash
   python refresh.py
   ```

2. **Knowledge Network** - Built graph
   ```bash
   python build_network.py
   ```

3. **Dependencies** - Python packages installed
   ```bash
   pip install python-pptx
   ```

### Generate All Agency Presentations

```bash
# From project root
python visualizations/presentation_generator.py
```

**Output**:
- Creates presentations for all agencies
- Both .md and .pptx files
- Saved to `presentations/{agency}/`

### Generate Specific Agency

```bash
# Generate for Department of Commerce
python visualizations/presentation_generator.py commerce

# Generate for Human Resources
python visualizations/presentation_generator.py human-resources

# Generate for Agriculture
python visualizations/presentation_generator.py agriculture
```

### Advanced Options

```bash
# Generate markdown only (skip PowerPoint)
python visualizations/presentation_generator.py --md-only

# Use custom graph path
python visualizations/presentation_generator.py --graph-path network/exports/custom_graph.pkl

# Verbose output
python visualizations/presentation_generator.py --verbose
```

## 🎯 Use Cases

### Public Outreach
- **Community Meetings** - Explain services to local communities
- **Public Forums** - Engage with citizens about agency programs
- **Town Halls** - Present agency updates and initiatives
- **Civic Education** - Teach about government services

### Internal Use
- **New Employee Orientation** - Introduce agency services
- **Inter-Agency Briefings** - Coordinate across departments
- **Training Sessions** - Educate staff on programs
- **Strategic Planning** - Review service portfolio

### External Presentations
- **Legislative Sessions** - Budget justifications and program updates
- **Grant Applications** - Demonstrate service delivery capacity
- **Partner Meetings** - Explain collaboration opportunities
- **Annual Reports** - Summarize agency activities

### Educational
- **School Presentations** - Civic education for students
- **University Lectures** - Guest presentations on government
- **Nonprofit Workshops** - Explain available resources
- **Media Briefings** - Background for journalists

## 📝 Editing Presentations

### Edit Markdown Source

Markdown files (`.md`) are the source content and can be manually edited:

```bash
# Open in text editor
nano presentations/commerce/commerce_presentation.md

# Or your preferred editor
code presentations/commerce/commerce_presentation.md
```

**Slide Separator**: Use `---` to separate slides

```markdown
## Slide Title

- Bullet point 1
- Bullet point 2

---

## Next Slide Title

Content here...
```

### Regenerate PowerPoint

After editing markdown, regenerate the PowerPoint:

```bash
python visualizations/presentation_generator.py commerce
```

### Add Custom Slides

Insert between `---` delimiters in the markdown file:

```markdown
---

## Our New Initiative

Montana is launching a new program to:
- Improve service delivery
- Increase accessibility
- Enhance citizen engagement

**Launch Date**: January 2026

---
```

## 🔄 Updating Presentations

When agency content changes on websites:

### Step 1: Refresh Content
```bash
# Update all agencies
python refresh.py

# Or specific agency
python refresh.py commerce
```

### Step 2: Rebuild Network
```bash
# Rebuild knowledge graph
python build_network.py
```

### Step 3: Regenerate Presentations
```bash
# All agencies
python visualizations/presentation_generator.py

# Or specific agency
python visualizations/presentation_generator.py commerce
```

## 🔧 Customization

### Modify Template

Edit `visualizations/presentation_generator.py`:

**Change Color Scheme**:
```python
# Around line 30
MONTANA_COLORS = {
    'primary': '#003F87',    # Your custom blue
    'secondary': '#4A90E2',  # Your custom accent
    'text': '#333333'        # Your custom text
}
```

**Adjust Slide Count**:
```python
# Around line 100
MAX_SLIDES = 20  # Change from default 15
SERVICES_PER_SLIDE = 5  # Adjust density
```

**Modify Content Extraction**:
```python
# Around line 200
def extract_services(graph, agency):
    # Customize RAG query
    # Filter results
    # Categorize differently
```

### Custom Branding

To add agency-specific branding:

1. Edit markdown template in generator
2. Add logo placement logic
3. Customize title slide layout
4. Modify footer with agency info

## 📈 Quality Assurance

### Automated Quality Checks

Each generated presentation:
- ✅ Sources content from official agency websites
- ✅ Organizes services into logical categories
- ✅ Applies professional Montana government styling
- ✅ Maintains 30-minute presentation length (15-20 slides)
- ✅ Provides both editable (markdown) and final (PowerPoint) formats
- ✅ Includes accurate contact and resource information

### Manual Review Recommended

Before presenting:
- Review for accuracy (content may be outdated if not recently crawled)
- Verify contact information is current
- Check for any formatting issues in PowerPoint
- Customize with agency-specific updates or announcements
- Add presenter notes if needed

## 🐛 Troubleshooting

### Issue: No Presentations Generated

**Problem**: Script runs but no files created

**Solutions**:
1. Check knowledge network exists:
   ```bash
   ls -la network/exports/montana_knowledge.pkl
   ```
2. If missing, build network:
   ```bash
   python build_network.py
   ```
3. Verify agency content exists:
   ```bash
   ls -la knowledge/commerce/
   ```

### Issue: Empty or Minimal Content

**Problem**: Presentation has few slides or limited content

**Solutions**:
1. Re-crawl agency website:
   ```bash
   python refresh.py commerce
   ```
2. Rebuild network:
   ```bash
   python build_network.py
   ```
3. Check if agency has substantial web content

### Issue: PowerPoint Not Created

**Problem**: Only markdown file generated, no .pptx

**Solutions**:
1. Install python-pptx:
   ```bash
   pip install python-pptx
   ```
2. Check for errors in output:
   ```bash
   python visualizations/presentation_generator.py commerce --verbose
   ```
3. Use `--md-only` flag to skip PowerPoint intentionally

### Issue: Formatting Problems

**Problem**: PowerPoint has layout issues

**Solutions**:
1. Check PowerPoint version (works best with Office 2016+)
2. Edit markdown and regenerate
3. Manually adjust in PowerPoint after generation
4. Modify template in `presentation_generator.py`

### Issue: Outdated Content

**Problem**: Presentation contains old information

**Solution**: Update pipeline
```bash
# 1. Refresh content from websites
python refresh.py

# 2. Rebuild knowledge graph
python build_network.py

# 3. Regenerate presentations
python visualizations/presentation_generator.py
```

## 🔗 Related Documentation

- **`../README.md`** - Master project documentation
- **`../visualizations/README.md`** - Visualization tools
- **`../network/README.md`** - Knowledge graph system
- **`../knowledge/README.md`** - Source content structure

## 📊 Technical Details

### Generation Process

1. **Load Knowledge Graph** - Read from `network/exports/`
2. **Query Services** - Use RAG retriever to find relevant content
3. **Categorize Services** - Group by type (Citizen, Business, Government)
4. **Extract Details** - Pull service descriptions, delivery methods
5. **Build Markdown** - Create structured markdown slides
6. **Convert to PowerPoint** - Use python-pptx library
7. **Apply Styling** - Montana government color scheme and fonts
8. **Save Files** - Both .md and .pptx to agency directory

### Dependencies
- **python-pptx** - PowerPoint file generation
- **NetworkX** - Graph data structure (via knowledge network)
- **Knowledge Graph** - Pre-built graph with all content

### File Sizes
- **Markdown**: 10-50 KB per presentation
- **PowerPoint**: 100-500 KB per presentation
- **Total Directory**: ~5-10 MB for all agencies

## 📄 File Formats

### Markdown (.md)
- Human-readable source format
- Easy to edit in any text editor
- Version control friendly
- Slides separated by `---`
- Supports standard markdown formatting

### PowerPoint (.pptx)
- Final presentation format
- Compatible with Microsoft Office, LibreOffice, Google Slides
- Professional styling applied
- Ready for immediate use
- Can be further customized in PowerPoint

## 📝 Best Practices

### Before Presenting
1. Review generated content for accuracy
2. Add agency-specific updates or announcements
3. Customize contact information if needed
4. Add presenter notes for complex topics
5. Test presentation on target computer/projector

### Maintaining Presentations
1. Update monthly or quarterly
2. Regenerate after major website changes
3. Archive old versions with dates
4. Track feedback for improvements
5. Share updates with other agencies

### Customization Guidelines
1. Maintain Montana government branding
2. Keep slides concise (5-7 bullets max)
3. Use clear, jargon-free language
4. Include visuals where appropriate (manually add)
5. Ensure accessibility (contrast, font size)

---

**Directory Purpose**: Generated agency service presentations  
**Generated By**: `visualizations/presentation_generator.py`  
**Update Frequency**: As needed (monthly recommended)  
**Format**: PowerPoint (.pptx) and Markdown (.md)  
**Last Updated**: December 2025
```bash
python visualizations/presentation_generator.py --agency commerce
python visualizations/presentation_generator.py --agency human-resources
```

### Generate Markdown Only (Skip PowerPoint)
```bash
python visualizations/presentation_generator.py --md-only
```

### Use Custom Graph Path
```bash
python visualizations/presentation_generator.py --graph-path network/exports/my_graph.pkl
```

## 📊 Presentation Content

Each 30-minute presentation includes approximately 15-20 slides:

1. **Title Slide** - Agency name and branding
2. **Agenda** - Overview of presentation topics
3. **Mission & Overview** - Agency purpose and role
4. **Citizen Services** - Services for individual residents
5. **Business Services** - Services for Montana businesses
6. **Government Services** - Inter-agency and governmental services
7. **Programs & Benefits** - Support programs and benefits
8. **Regulations & Compliance** - Regulatory requirements
9. **Resources & Information** - Guides, forms, and documentation
10. **Key Service Areas** - Most common service topics
11. **How to Access Services** - Online, in-person, phone, mail
12. **Contact Information** - Website, phone, office locations
13. **Thank You / Q&A** - Closing slide

## 🔧 Requirements

- Python 3.9+
- Knowledge network built (run `python build_network.py`)
- python-pptx library (for PowerPoint generation)

```bash
pip install python-pptx
```

## 📝 Editing Presentations

### Markdown Files
The `.md` files are the source content and can be edited directly:
- Edit service descriptions
- Add or remove slides (separate with `---`)
- Update contact information
- Modify mission statements

### Regenerate PowerPoint
After editing markdown:
```bash
python visualizations/presentation_generator.py --agency <agency-name>
```

## 🎯 Use Cases

- **Public Presentations** - Community meetings, public forums
- **New Employee Orientations** - Explaining agency services
- **Inter-Agency Briefings** - Coordinating across departments
- **Legislative Sessions** - Budget and program justifications
- **Citizen Education** - Explaining government services
- **Grant Applications** - Demonstrating service delivery
- **Annual Reports** - Summarizing agency activities

## 📊 Customization

### Modify Presentation Template
Edit `visualizations/presentation_generator.py`:
- `MarkdownPresentationGenerator._create_markdown_slides()` - Content and structure
- `PowerPointConverter.MONTANA_COLORS` - Color scheme
- `PowerPointConverter._create_slide()` - Slide formatting

### Add Custom Slides
Insert in markdown between `---` delimiters:
```markdown
---

## Custom Slide Title

- Bullet point 1
- Bullet point 2
- Bullet point 3

---
```

## 🔄 Updating Presentations

When agency content changes:

1. **Refresh knowledge base**:
   ```bash
   python refresh.py
   ```

2. **Rebuild knowledge network**:
   ```bash
   python build_network.py
   ```

3. **Regenerate presentations**:
   ```bash
   python visualizations/presentation_generator.py
   ```

## 📈 Quality Assurance

Each presentation is:
- ✅ Automatically generated from official agency content
- ✅ Organized into logical service categories
- ✅ Formatted with professional Montana government branding
- ✅ Suitable for 30-minute delivery (15-20 slides)
- ✅ Available in both markdown and PowerPoint formats
- ✅ Based on actual agency website content and documents

## 🆘 Troubleshooting

### No Content Generated
- Ensure knowledge network is built: `python build_network.py`
- Check agency folder exists in `knowledge/` directory
- Verify agency has crawled content

### PowerPoint Not Generated
- Install python-pptx: `pip install python-pptx`
- Use `--md-only` flag to skip PowerPoint generation
- Check for errors in terminal output

### Missing Services
- Re-crawl agency website: `python refresh.py`
- Rebuild network: `python build_network.py`
- Check RAG retrieval is working correctly

## 📞 Support

For questions or issues:
1. Check the main project README.md
2. Review network/README.md for knowledge network details
3. Examine terminal output for specific errors
4. Verify all dependencies are installed

## 🎓 Technical Details

The presentation generator uses:
- **Knowledge Graph** - NetworkX graph of all agency documents
- **RAG Retrieval** - Semantic search to find relevant content
- **Content Analysis** - Categorizes services by type and audience
- **Markdown Generation** - Creates structured presentation content
- **PowerPoint Conversion** - Uses python-pptx library for PPTX files
- **Montana Branding** - Official state government color palette

---

**Generated by Montana State Government Knowledge System**
*Serving Montana Citizens Through Technology*
