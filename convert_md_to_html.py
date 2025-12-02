#!/usr/bin/env python3
"""
Markdown to HTML Converter with Mermaid Diagram Support
Converts FPO_AP_STATE_COMPLETE_GUIDE.md to HTML with all 49 Mermaid diagrams preserved.
"""

import re
import html
import os
import sys
from pathlib import Path

def slugify(text):
    """Convert text to URL-friendly slug for heading IDs."""
    # Remove emojis and special characters, keep alphanumeric and spaces
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[-\s]+', '-', text).strip('-')
    return text

def escape_html_except_tags(text):
    """Escape HTML special characters but preserve certain patterns."""
    # Don't escape if it's already HTML or special markdown
    return text

def convert_inline_formatting(text):
    """Convert inline markdown formatting to HTML."""
    # Bold: **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    
    # Italic: *text* or _text_ (but not inside words)
    text = re.sub(r'(?<!\w)\*(?!\*)(.+?)(?<!\*)\*(?!\w)', r'<em>\1</em>', text)
    text = re.sub(r'(?<!\w)_(?!_)(.+?)(?<!_)_(?!\w)', r'<em>\1</em>', text)
    
    # Inline code: `code`
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    
    # Links: [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    
    # Auto-link bare URLs (http:// and https://) - but not if already inside an <a> tag
    # Match URLs that are not already inside href=""
    text = re.sub(
        r'(?<!href=")(?<!href=\')(?<!")(https?://[^\s<>"\'\)\]]+)',
        r'<a href="\1" target="_blank">\1</a>',
        text
    )
    
    # Strikethrough: ~~text~~
    text = re.sub(r'~~(.+?)~~', r'<del>\1</del>', text)
    
    return text

def convert_table(lines):
    """Convert markdown table to HTML table."""
    if len(lines) < 2:
        return '<p>' + '<br>'.join(lines) + '</p>'
    
    html_parts = ['<table>']
    
    # Check if second line is separator (contains |---|)
    is_header = bool(re.match(r'^\s*\|?\s*[-:]+\s*\|', lines[1]))
    
    for i, line in enumerate(lines):
        # Skip separator line
        if i == 1 and is_header:
            continue
        
        # Clean the line
        line = line.strip()
        if line.startswith('|'):
            line = line[1:]
        if line.endswith('|'):
            line = line[:-1]
        
        cells = [cell.strip() for cell in line.split('|')]
        
        if i == 0 and is_header:
            html_parts.append('<thead><tr>')
            for cell in cells:
                html_parts.append(f'<th>{convert_inline_formatting(cell)}</th>')
            html_parts.append('</tr></thead><tbody>')
        else:
            html_parts.append('<tr>')
            for cell in cells:
                html_parts.append(f'<td>{convert_inline_formatting(cell)}</td>')
            html_parts.append('</tr>')
    
    if is_header:
        html_parts.append('</tbody>')
    html_parts.append('</table>')
    
    return '\n'.join(html_parts)

def process_list(lines, start_idx):
    """Process a list (ordered or unordered) and return HTML and end index."""
    html_parts = []
    i = start_idx
    
    # Determine list type and starting number
    first_line = lines[i].lstrip()
    ordered_match = re.match(r'^(\d+)\.', first_line)
    is_ordered = bool(ordered_match)
    tag = 'ol' if is_ordered else 'ul'
    
    # For ordered lists, preserve the start number if not 1
    if is_ordered and ordered_match:
        start_num = int(ordered_match.group(1))
        if start_num != 1:
            html_parts.append(f'<{tag} start="{start_num}">')
        else:
            html_parts.append(f'<{tag}>')
    else:
        html_parts.append(f'<{tag}>')
    
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        
        # Check if still a list item
        if is_ordered:
            match = re.match(r'^(\d+)\.\s+(.*)$', stripped)
        else:
            match = re.match(r'^[-*+]\s+(.*)$', stripped)
        
        if not match:
            # Check for continuation or nested content
            if line.startswith('  ') or line.startswith('\t'):
                # Continuation of previous item
                if html_parts and html_parts[-1].endswith('</li>'):
                    html_parts[-1] = html_parts[-1][:-5]  # Remove </li>
                    html_parts.append(f'<br>{convert_inline_formatting(stripped)}')
                    html_parts.append('</li>')
                i += 1
                continue
            else:
                break
        
        if is_ordered:
            content = match.group(2)
        else:
            content = match.group(1)
        
        html_parts.append(f'<li>{convert_inline_formatting(content)}</li>')
        i += 1
    
    html_parts.append(f'</{tag}>')
    return '\n'.join(html_parts), i

def convert_markdown_to_html(markdown_content):
    """Convert markdown content to HTML."""
    lines = markdown_content.split('\n')
    html_parts = []
    i = 0
    in_code_block = False
    code_block_content = []
    code_block_lang = ''
    mermaid_count = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Handle code blocks (including mermaid)
        if line.strip().startswith('```'):
            if not in_code_block:
                # Start of code block
                in_code_block = True
                lang_match = re.match(r'^```(\w*)', line.strip())
                code_block_lang = lang_match.group(1) if lang_match else ''
                code_block_content = []
                i += 1
                continue
            else:
                # End of code block
                in_code_block = False
                content = '\n'.join(code_block_content)
                
                if code_block_lang.lower() == 'mermaid':
                    mermaid_count += 1
                    # Mermaid diagram - use div with class mermaid
                    html_parts.append(f'<div class="mermaid">\n{content}\n</div>')
                else:
                    # Regular code block
                    escaped_content = html.escape(content)
                    if code_block_lang:
                        html_parts.append(f'<pre><code class="language-{code_block_lang}">{escaped_content}</code></pre>')
                    else:
                        html_parts.append(f'<pre><code>{escaped_content}</code></pre>')
                
                code_block_content = []
                code_block_lang = ''
                i += 1
                continue
        
        if in_code_block:
            code_block_content.append(line)
            i += 1
            continue
        
        # Handle headings
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            slug = slugify(text)
            formatted_text = convert_inline_formatting(text)
            html_parts.append(f'<h{level} id="{slug}">{formatted_text}</h{level}>')
            i += 1
            continue
        
        # Handle horizontal rules
        if re.match(r'^[-*_]{3,}\s*$', line.strip()):
            html_parts.append('<hr>')
            i += 1
            continue
        
        # Handle blockquotes
        if line.strip().startswith('>'):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                quote_content = re.sub(r'^>\s?', '', lines[i])
                quote_lines.append(convert_inline_formatting(quote_content))
                i += 1
            html_parts.append(f'<blockquote><p>{"<br>".join(quote_lines)}</p></blockquote>')
            continue
        
        # Handle tables
        if '|' in line and i + 1 < len(lines) and '|' in lines[i + 1]:
            table_lines = []
            while i < len(lines) and '|' in lines[i]:
                table_lines.append(lines[i])
                i += 1
            html_parts.append(convert_table(table_lines))
            continue
        
        # Handle unordered lists
        if re.match(r'^[-*+]\s+', line.lstrip()):
            list_html, i = process_list(lines, i)
            html_parts.append(list_html)
            continue
        
        # Handle ordered lists
        if re.match(r'^\d+\.\s+', line.lstrip()):
            list_html, i = process_list(lines, i)
            html_parts.append(list_html)
            continue
        
        # Handle checkbox items
        checkbox_match = re.match(r'^[-*]\s+\[([ xX])\]\s+(.*)$', line.strip())
        if checkbox_match:
            checked = checkbox_match.group(1).lower() == 'x'
            text = checkbox_match.group(2)
            check_html = '☑' if checked else '☐'
            html_parts.append(f'<p class="checkbox">{check_html} {convert_inline_formatting(text)}</p>')
            i += 1
            continue
        
        # Handle empty lines
        if not line.strip():
            html_parts.append('')
            i += 1
            continue
        
        # Handle regular paragraphs
        para_lines = []
        while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith('#') and not lines[i].strip().startswith('```') and not re.match(r'^[-*_]{3,}\s*$', lines[i].strip()) and not lines[i].strip().startswith('>') and '|' not in lines[i]:
            # Check if next line starts a list
            if re.match(r'^[-*+]\s+', lines[i].lstrip()) or re.match(r'^\d+\.\s+', lines[i].lstrip()):
                break
            para_lines.append(lines[i])
            i += 1
        
        if para_lines:
            para_text = ' '.join(para_lines)
            html_parts.append(f'<p>{convert_inline_formatting(para_text)}</p>')
        else:
            i += 1
    
    print(f"Found and converted {mermaid_count} Mermaid diagrams")
    return '\n'.join(html_parts), mermaid_count

def create_html_document(body_content, title="FPO AP State Complete Guide"):
    """Create a complete HTML document with styling and Mermaid.js."""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    
    <!-- Mermaid.js -->
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }},
            sequence: {{
                useMaxWidth: true
            }},
            gantt: {{
                useMaxWidth: true
            }},
            pie: {{
                useMaxWidth: true
            }},
            graph: {{
                useMaxWidth: true
            }}
        }});
    </script>
    
    <style>
        /* Base styles */
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.8;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px 40px;
            color: #333;
            background-color: #fff;
        }}
        
        /* Headings */
        h1, h2, h3, h4, h5, h6 {{
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            font-weight: 600;
            line-height: 1.3;
            color: #1a1a1a;
        }}
        
        h1 {{
            font-size: 2.5em;
            border-bottom: 3px solid #2563eb;
            padding-bottom: 0.3em;
            color: #1e40af;
        }}
        
        h2 {{
            font-size: 2em;
            border-bottom: 2px solid #3b82f6;
            padding-bottom: 0.2em;
            color: #1e40af;
        }}
        
        h3 {{
            font-size: 1.5em;
            color: #2563eb;
        }}
        
        h4 {{
            font-size: 1.25em;
            color: #3b82f6;
        }}
        
        h5 {{
            font-size: 1.1em;
            color: #60a5fa;
        }}
        
        h6 {{
            font-size: 1em;
            color: #93c5fd;
        }}
        
        /* Paragraphs */
        p {{
            margin: 1em 0;
            text-align: justify;
        }}
        
        /* Links */
        a {{
            color: #2563eb;
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
            color: #1d4ed8;
        }}
        
        /* Lists */
        ul, ol {{
            margin: 1em 0;
            padding-left: 2em;
        }}
        
        li {{
            margin: 0.5em 0;
        }}
        
        /* Tables */
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1.5em 0;
            font-size: 0.95em;
            overflow-x: auto;
            display: block;
        }}
        
        th, td {{
            border: 1px solid #d1d5db;
            padding: 12px 15px;
            text-align: left;
        }}
        
        th {{
            background-color: #2563eb;
            color: white;
            font-weight: 600;
        }}
        
        tr:nth-child(even) {{
            background-color: #f3f4f6;
        }}
        
        tr:hover {{
            background-color: #e5e7eb;
        }}
        
        /* Code blocks */
        pre {{
            background-color: #1e293b;
            color: #e2e8f0;
            padding: 1.5em;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 0.9em;
            line-height: 1.5;
            margin: 1.5em 0;
        }}
        
        code {{
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        }}
        
        p code, li code, td code {{
            background-color: #f1f5f9;
            color: #dc2626;
            padding: 0.2em 0.4em;
            border-radius: 4px;
            font-size: 0.9em;
        }}
        
        pre code {{
            background: none;
            color: inherit;
            padding: 0;
        }}
        
        /* Blockquotes */
        blockquote {{
            border-left: 4px solid #2563eb;
            margin: 1.5em 0;
            padding: 1em 1.5em;
            background-color: #eff6ff;
            color: #1e40af;
        }}
        
        blockquote p {{
            margin: 0;
        }}
        
        /* Horizontal rules */
        hr {{
            border: none;
            border-top: 2px solid #e5e7eb;
            margin: 2em 0;
        }}
        
        /* Mermaid diagrams */
        .mermaid {{
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin: 2em 0;
            text-align: center;
            overflow-x: auto;
        }}
        
        .mermaid svg {{
            max-width: 100%;
            height: auto;
        }}
        
        /* Checkbox styling */
        .checkbox {{
            font-family: inherit;
        }}
        
        /* Strong and emphasis */
        strong {{
            font-weight: 700;
            color: #1a1a1a;
        }}
        
        em {{
            font-style: italic;
        }}
        
        /* Delete/strikethrough */
        del {{
            text-decoration: line-through;
            color: #6b7280;
        }}
        
        /* Print styles */
        @media print {{
            body {{
                max-width: none;
                padding: 0;
                font-size: 11pt;
            }}
            
            pre {{
                white-space: pre-wrap;
                word-wrap: break-word;
            }}
            
            table {{
                page-break-inside: avoid;
            }}
            
            h1, h2, h3, h4, h5, h6 {{
                page-break-after: avoid;
            }}
            
            .mermaid {{
                page-break-inside: avoid;
            }}
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            body {{
                padding: 15px;
            }}
            
            h1 {{
                font-size: 1.8em;
            }}
            
            h2 {{
                font-size: 1.5em;
            }}
            
            table {{
                font-size: 0.85em;
            }}
            
            th, td {{
                padding: 8px 10px;
            }}
        }}
    </style>
</head>
<body>
{body_content}

<script>
    // Re-initialize Mermaid after page load to ensure all diagrams render
    document.addEventListener('DOMContentLoaded', function() {{
        setTimeout(function() {{
            mermaid.init(undefined, document.querySelectorAll('.mermaid'));
        }}, 500);
    }});
</script>
</body>
</html>'''

def main():
    # File paths
    input_file = Path("c:/FPO_Complete_Guide.md/FPO_AP_STATE_COMPLETE_GUIDE.md")
    output_file = Path("c:/FPO_Complete_Guide.md/FPO_AP_STATE_COMPLETE_GUIDE.html")
    
    print(f"Reading markdown file: {input_file}")
    
    # Check if input file exists
    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}")
        sys.exit(1)
    
    # Read the markdown file
    with open(input_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    lines = markdown_content.split('\n')
    print(f"Read {len(lines)} lines from markdown file")
    
    # Convert markdown to HTML
    print("Converting markdown to HTML...")
    body_content, mermaid_count = convert_markdown_to_html(markdown_content)
    
    # Create complete HTML document
    html_content = create_html_document(body_content)
    
    # Write HTML file
    print(f"Writing HTML file: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Get file sizes
    input_size = input_file.stat().st_size
    output_size = output_file.stat().st_size
    
    print(f"\n{'='*60}")
    print("CONVERSION COMPLETE!")
    print(f"{'='*60}")
    print(f"Input file:  {input_file}")
    print(f"Input size:  {input_size:,} bytes ({input_size/1024:.1f} KB)")
    print(f"Input lines: {len(lines):,}")
    print(f"Output file: {output_file}")
    print(f"Output size: {output_size:,} bytes ({output_size/1024:.1f} KB)")
    print(f"Mermaid diagrams found: {mermaid_count}")
    print(f"{'='*60}")
    
    # Verify mermaid count
    with open(output_file, 'r', encoding='utf-8') as f:
        html_output = f.read()
    
    mermaid_divs = len(re.findall(r'<div class="mermaid">', html_output))
    print(f"\nVerification: Found {mermaid_divs} <div class=\"mermaid\"> blocks in HTML")
    
    if mermaid_divs == 49:
        print("✅ SUCCESS: All 49 Mermaid diagrams preserved!")
    else:
        print(f"⚠️ WARNING: Expected 49 Mermaid diagrams, found {mermaid_divs}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
