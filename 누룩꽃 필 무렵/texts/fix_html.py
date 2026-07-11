import re

file_path = "단서.txt"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Notice HTMLs
notice_know = """    <div class="guide-notice type-info">
      아는 정보들은 이번 단계에서 반드시 공개되어야 합니다. 대화의 흐름에 따라 자연스럽게 이야기하세요.
    </div>"""

notice_secret = """    <div class="guide-notice type-warning">
      당신의 비밀들은 타인에게 추궁받거나 지적받았을 때만 마지못해 이야기 할 수 있습니다. 이번 단계에서 모든 비밀을 이야기해야 다음 단계로 진행할 수 있으니, 아무도 당신의 비밀에 대해 묻지 않는다면 대화의 흐름을 자연스럽게 이 주제로 이끌어보세요. 그럼 누군가는 당신에게 질문을 할 것입니다.
    </div>"""

def process_html_block(html_block, is_know, is_secret):
    # Fix indentation for <ul> and <li>
    # Usually it's:
    #     <ul>
    #     <li>...</li>
    #   </ul>
    # Should be:
    #     <ul>
    #       <li>...</li>
    #     </ul>
    lines = html_block.split("\n")
    fixed_lines = []
    in_ul = False
    for line in lines:
        if re.search(r'^\s*<ul>', line):
            in_ul = True
            fixed_lines.append("    <ul>")
        elif re.search(r'^\s*</ul>', line):
            in_ul = False
            fixed_lines.append("    </ul>")
        elif in_ul and re.search(r'^\s*<li>', line):
            # replace leading whitespace with 6 spaces
            line = re.sub(r'^\s*<li>', '      <li>', line)
            fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    html_block = "\n".join(fixed_lines)

    # Check if the required notice is missing
    target_notice = None
    if is_know:
        target_notice = notice_know
    elif is_secret:
        target_notice = notice_secret
    
    if target_notice:
        # Check if notice already exists
        if "guide-notice type-info" not in html_block and is_know:
            needs_insert = True
        elif "guide-notice type-warning" not in html_block and is_secret:
            needs_insert = True
        else:
            needs_insert = False
            
        if needs_insert:
            # We want to insert the target_notice just before the last </div></div>
            # Let's find the innermost container that wraps the text.
            # It's usually `<div class="document-page ...">`
            # The structure is usually:
            # <div class="story-content">
            #   <div class="document-page ...">
            #     ...
            #   </div>
            # </div>
            # So we can insert right before the last `  </div>\n</div>`
            
            # Find the index of the last `  </div>`
            match = list(re.finditer(r'^\s*</div>\s*$', html_block, flags=re.MULTILINE))
            if len(match) >= 2:
                # The second to last closing div is for `document-page`
                insert_pos = match[-2].start()
                html_block = html_block[:insert_pos] + target_notice + "\n" + html_block[insert_pos:]
            
    return html_block

clues = content.split("### [clue_")
new_clues = []

for i, clue in enumerate(clues):
    if i == 0:
        new_clues.append(clue)
        continue
    
    is_know = bool(re.search(r'^이름\s*:\s*당신이 아는 것', clue, flags=re.MULTILINE))
    is_secret = bool(re.search(r'^이름\s*:\s*당신의 비밀', clue, flags=re.MULTILINE))
    
    # Extract HTML part
    html_match = re.search(r'(HTML\s*:\s*\n)(<div class="story-content">.*?\n</div>\s*\n)(이미지생성용 프롬프트:)', clue, flags=re.DOTALL)
    if html_match and (is_know or is_secret):
        prefix = html_match.group(1)
        html_block = html_match.group(2)
        suffix = html_match.group(3)
        
        new_html_block = process_html_block(html_block, is_know, is_secret)
        
        # Replace the HTML part in the clue
        clue = clue[:html_match.start()] + prefix + new_html_block + suffix + clue[html_match.end():]
    
    new_clues.append(clue)

new_content = "### [clue_".join(new_clues)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Done processing.")