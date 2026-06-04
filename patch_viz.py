#!/usr/bin/env python3
"""Patch the agency_network_viz.py file to use static 2D layout"""

import re

file_path = "src/visualizations/agency_network_viz.py"

with open(file_path, 'r') as f:
    content = f.read()

# Find the first occurrence (in generate_agency_selector_html_dynamic)
# We'll replace from line ~820 onwards in the JS section

# 1. Add truncateText function after typeColors
pattern1 = r'(const typeColors = \{\{[^}]+\}\};)\s+(// Agency selection handler)'
replacement1 = r'''\1
        
        // Truncate text to fit within circle
        function truncateText(text, radius, scale = 1) {{
            const charsPerPixel = 0.15 * scale;
            const maxChars = Math.floor(radius * 2 * charsPerPixel);
            if (text.length <= maxChars) return text;
            return text.substring(0, Math.max(3, maxChars - 3)) + '...';
        }}
        
        \2'''

# 2. Replace force simulation with static layout
pattern2 = r'(svg\.call\(zoom\);)\s+// Force simulation[\s\S]+?(?=// Draw links)'
replacement2 = r'''\1
            
            // Static circular layout (no physics simulation)
            const centerX = width / 2;
            const centerY = height / 2;
            
            // Separate nodes by type
            const agencyNodes = nodesData.filter(d => d.is_agency);
            const navigationNodes = nodesData.filter(d => !d.is_agency && d.is_navigation);
            const secondaryNodes = nodesData.filter(d => !d.is_agency && !d.is_navigation);
            
            // Position agency nodes at center
            agencyNodes.forEach((d, i) => {{
                const angle = (i / agencyNodes.length) * 2 * Math.PI;
                const radius = 50;
                d.x = centerX + radius * Math.cos(angle);
                d.y = centerY + radius * Math.sin(angle);
                d.fx = d.x;
                d.fy = d.y;
            }});
            
            // Position navigation nodes in first ring
            navigationNodes.forEach((d, i) => {{
                const angle = (i / navigationNodes.length) * 2 * Math.PI;
                const radius = Math.min(width, height) * 0.25;
                d.x = centerX + radius * Math.cos(angle);
                d.y = centerY + radius * Math.sin(angle);
                d.fx = d.x;
                d.fy = d.y;
            }});
            
            // Position secondary nodes in outer ring
            secondaryNodes.forEach((d, i) => {{
                const angle = (i / secondaryNodes.length) * 2 * Math.PI;
                const radius = Math.min(width, height) * 0.4;
                d.x = centerX + radius * Math.cos(angle);
                d.y = centerY + radius * Math.sin(angle);
                d.fx = d.x;
                d.fy = d.y;
            }});
            
            // Create a stopped simulation just to handle dragging
            simulation = d3.forceSimulation(nodesData)
                .force("link", d3.forceLink(linksData).id(d => d.index).strength(0))
                .stop();
            
            '''

# 3. Update zoom handler
pattern3 = r'(const zoom = d3\.zoom\(\)[\s\S]+?\.on\("zoom", \(event\) => \{\{)\s+(g\.attr\("transform", event\.transform\);)\s+(updateLabelVisibility\(event\.transform\.k\);)\s+(\}\}\);)'
replacement3 = r'''\1
                    \2
                    const scale = event.transform.k;
                    // Update labels on zoom
                    if (window.currentElements && window.currentElements.label) {{
                        window.currentElements.label
                            .text(d => truncateText(d.title, d.size, scale))
                            .style("font-size", d => {{
                                const baseFontSize = d.is_agency ? 13 : (d.is_navigation ? 11 : 10);
                                return Math.min(baseFontSize, d.size * 0.3) + "px";
                            }});
                    }}
                \4'''

# 4. Update labels to be inside circles
pattern4 = r'(// Draw labels[\s\S]+?\.join\("text"\)[\s\S]+?\.attr\("class", d => \{\{[\s\S]+?\}\}\))\s+\.text\(d => d\.title\.length > 30 \? d\.title\.substring\(0, 30\) \+ "\.\.\." : d\.title\)\s+\.attr\("dx", d => d\.size \+ 5\)\s+\.attr\("dy", 4\);'
replacement4 = r'''\1
                .attr("text-anchor", "middle")
                .attr("dominant-baseline", "middle")
                .text(d => truncateText(d.title, d.size))
                .attr("dx", 0)
                .attr("dy", 0)
                .style("font-size", d => {{
                    const baseFontSize = d.is_agency ? 13 : (d.is_navigation ? 11 : 10);
                    return Math.min(baseFontSize, d.size * 0.3) + "px";
                }});'''

# 5. Replace simulation tick with static rendering
pattern5 = r'// Simulation tick\s+simulation\.on\("tick", \(\) => \{\{[\s\S]+?\}\}\);'
replacement5 = r'''// Initial render (static positions already set)
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            
            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);
            
            label
                .attr("x", d => d.x)
                .attr("y", d => d.y);'''

# 6. Update drag handlers
pattern6 = r'function dragstarted\(event, d\) \{\{[\s\S]+?\}\}\s+function dragged\(event, d\) \{\{[\s\S]+?\}\}\s+function dragended\(event, d\) \{\{[\s\S]+?\}\}'
replacement6 = r'''function dragstarted(event, d) {{
            d3.select(event.sourceEvent.target).raise();
        }}
        
        function dragged(event, d) {{
            d.x = event.x;
            d.y = event.y;
            d.fx = event.x;
            d.fy = event.y;
            
            // Update visual positions
            d3.select(event.sourceEvent.target).attr("cx", d.x).attr("cy", d.y);
            
            // Update connected edges
            if (window.currentElements && window.currentElements.link) {{
                window.currentElements.link
                    .filter(l => l.source === d || l.target === d)
                    .attr("x1", l => l.source.x)
                    .attr("y1", l => l.source.y)
                    .attr("x2", l => l.target.x)
                    .attr("y2", l => l.target.y);
            }}
            
            // Update label
            if (window.currentElements && window.currentElements.label) {{
                window.currentElements.label
                    .filter(l => l === d)
                    .attr("x", d.x)
                    .attr("y", d.y);
            }}
        }}
        
        function dragended(event, d) {{
            // Keep position fixed after drag
        }}'''

# 7. Update togglePhysics
pattern7 = r'function togglePhysics\(\) \{\{[\s\S]+?if \(simulation\) \{\{[\s\S]+?\}\}\s+\}\}'
replacement7 = r'''function togglePhysics() {{
            // Physics is disabled for static layout
            alert('This visualization uses a static layout. Use drag to reposition nodes.');
        }}'''

# 8. Update CSS for labels
pattern8 = r'\.label \{\{[\s\S]+?fill: #2d3748;[\s\S]+?text-shadow: 1px 1px 2px white[^}]+\}\}\s+\.label\.important \{\{[\s\S]+?fill: #1a202c;[\s\S]+?\}\}\s+\.label\.secondary \{\{[\s\S]+?opacity: 0\.7;[\s\S]+?\}\}'
replacement8 = r'''.label {{
            font-size: 11px;
            font-weight: 600;
            fill: #ffffff;
            pointer-events: none;
            user-select: none;
            text-shadow: 0px 0px 3px rgba(0,0,0,0.8), 0px 0px 6px rgba(0,0,0,0.6);
        }}
        
        .label.important {{
            font-size: 13px;
            font-weight: 700;
            fill: #ffffff;
        }}
        
        .label.secondary {{
            font-size: 10px;
            font-weight: 500;
            fill: #ffffff;
            opacity: 0.9;
        }}'''

# Apply all replacements
print("Applying patches...")
changes_made = 0

if re.search(pattern1, content):
    content = re.sub(pattern1, replacement1, content, count=1)
    print("✓ Added truncateText function")
    changes_made += 1
else:
    print("✗ Could not find pattern for truncateText")

if re.search(pattern2, content):
    content = re.sub(pattern2, replacement2, content, count=1)
    print("✓ Replaced force simulation with static layout")
    changes_made += 1
else:
    print("✗ Could not find pattern for static layout")

if re.search(pattern3, content):
    content = re.sub(pattern3, replacement3, content, count=1)
    print("✓ Updated zoom handler")
    changes_made += 1
else:
    print("✗ Could not find pattern for zoom handler")

if re.search(pattern4, content):
    content = re.sub(pattern4, replacement4, content, count=1)
    print("✓ Updated labels to be inside circles")
    changes_made += 1
else:
    print("✗ Could not find pattern for labels")

if re.search(pattern5, content):
    content = re.sub(pattern5, replacement5, content, count=1)
    print("✓ Replaced simulation tick with static rendering")
    changes_made += 1
else:
    print("✗ Could not find pattern for simulation tick")

if re.search(pattern6, content):
    content = re.sub(pattern6, replacement6, content, count=1)
    print("✓ Updated drag handlers")
    changes_made += 1
else:
    print("✗ Could not find pattern for drag handlers")

if re.search(pattern7, content):
    content = re.sub(pattern7, replacement7, content, count=1)
    print("✓ Updated togglePhysics")
    changes_made += 1
else:
    print("✗ Could not find pattern for togglePhysics")

if re.search(pattern8, content):
    content = re.sub(pattern8, replacement8, content, count=1)
    print("✓ Updated label CSS")
    changes_made += 1
else:
    print("✗ Could not find pattern for label CSS")

# Write the modified content
if changes_made > 0:
    with open(file_path, 'w') as f:
        f.write(content)
    print(f"\n✅ Applied {changes_made}/8 patches successfully!")
else:
    print("\n❌ No patches were applied. File may have already been modified.")
