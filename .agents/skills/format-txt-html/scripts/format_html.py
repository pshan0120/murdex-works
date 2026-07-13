import sys
import os
import subprocess
import re

def format_html_in_txt(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File not found - {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fragments = []
    text_parts = [] # store lines that are not HTML
    
    in_html_block = False
    html_buffer = []
    current_text_buffer = []

    for line in lines:
        stripped = line.strip()

        if not in_html_block and stripped.startswith('<div'):
            in_html_block = True
            text_parts.append(current_text_buffer)
            current_text_buffer = []
            html_buffer.append(line)
            continue
            
        if in_html_block:
            # End of HTML block is explicitly defined by Murdex file structure
            if stripped == '' or re.match(r'^(이미지생성용 프롬프트|장소|파일명|관련|의도|내용|HTML)\s*:', stripped) or re.match(r'^\d+\.\s+', stripped) or stripped.startswith('###') or stripped.startswith('---'):
                fragments.append(html_buffer)
                current_text_buffer.append(line)
                in_html_block = False
                html_buffer = []
            else:
                html_buffer.append(line)
        else:
            current_text_buffer.append(line)
            
    if in_html_block:
        fragments.append(html_buffer)
        current_text_buffer = []
        
    text_parts.append(current_text_buffer)

    if not fragments:
        print(f"No HTML blocks found in {file_path}")
        return

    # Combine all fragments into one temp file
    temp_file = file_path + ".temp.html"
    combined_html = ""
    for i, frag in enumerate(fragments):
        combined_html += f"<!-- FRAGMENT_START_{i} -->\n"
        combined_html += "".join(frag)
        combined_html += f"<!-- FRAGMENT_END_{i} -->\n"

    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(combined_html)

    # Run Prettier
    try:
        # Run prettier on the temp file
        result = subprocess.run(["npx.cmd", "prettier", "--write", "--print-width", "120", temp_file], check=True, capture_output=True, text=True, encoding='utf-8')
    except subprocess.CalledProcessError as e:
        print(f"Prettier formatting failed: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return

    # Read formatted HTML
    with open(temp_file, 'r', encoding='utf-8') as f:
        formatted_html = f.read()

    os.remove(temp_file)

    # Reconstruct
    out_lines = []
    
    for i in range(len(fragments)):
        out_lines.extend(text_parts[i])
        
        # Extract formatted fragment i
        # Prettier formats comments, so they might have spaces: <!-- FRAGMENT_START_0 -->
        pattern = f"<!--\\s*FRAGMENT_START_{i}\\s*-->\\n(.*?)\\n<!--\\s*FRAGMENT_END_{i}\\s*-->"
        match = re.search(pattern, formatted_html, re.DOTALL)
        if match:
            frag_content = match.group(1)
            # Ensure lines end with newline
            frag_lines = [line + '\n' for line in frag_content.split('\n')]
            out_lines.extend(frag_lines)
        else:
            print(f"Warning: Could not extract fragment {i}, keeping original.")
            out_lines.extend(fragments[i])

    out_lines.extend(text_parts[-1])

    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(out_lines)
    
    print(f"Successfully formatted HTML in {file_path} using Prettier")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python format_html.py <file_path>")
        sys.exit(1)
        
    format_html_in_txt(sys.argv[1])
