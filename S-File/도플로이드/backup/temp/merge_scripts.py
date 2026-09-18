import re
import os

def process_scripts():
    base_path = r'c:\dev\KLIEN\murdex\works\도플로이드\texts'
    output_file = os.path.join(base_path, '대본_전체.txt')
    
    combined_content = []
    
    # Updated Regex: Support characters like "레바(A)", "니악(C)", etc.
    pattern = re.compile(
        r'<div class="script-line (?:my-line|other-character)">\s*<span class="script-character(?: my-character)?">(.*?)</span>:\s*"(.*?)"\s*</div>',
        re.DOTALL
    )
    
    for i in range(1, 12):
        file_a = os.path.join(base_path, f'대본_서사{i}_A.txt')
        file_c = os.path.join(base_path, f'대본_서사{i}_C.txt')
        
        if not os.path.exists(file_a) or not os.path.exists(file_c):
            continue
            
        with open(file_a, 'r', encoding='utf-8') as f:
            content_a = f.read()
        with open(file_c, 'r', encoding='utf-8') as f:
            content_c = f.read()
            
        lines_a = pattern.findall(content_a)
        lines_c = pattern.findall(content_c)
        
        merged_narrative = []
        merged_narrative.append(f"========================================")
        merged_narrative.append(f"               서사 {i}")
        merged_narrative.append(f"========================================")
        
        num_lines = max(len(lines_a), len(lines_c))
        
        for idx in range(num_lines):
            char_a_label, text_a = lines_a[idx] if idx < len(lines_a) else ("", "")
            char_c_label, text_c = lines_c[idx] if idx < len(lines_c) else ("", "")
            
            # Identify which character is speaking based on the label
            # Labels can be "A", "C", "레바(A)", "니악(C)", etc.
            is_a_speaking = 'A' in char_a_label or '레바' in char_a_label
            is_c_speaking = 'C' in char_c_label or '니악' in char_c_label
            
            # File A: Complete text for A, placeholder for C
            # File C: Complete text for C, placeholder for A
            
            if is_a_speaking:
                # This turn belongs to A
                final_char = char_a_label
                final_text = text_a
            else:
                # This turn belongs to C
                final_char = char_c_label
                final_text = text_c
            
            # Clean up
            final_text = final_text.replace('&nbsp;', '').strip()
            merged_narrative.append(f"{final_char}: {final_text}")
            
        combined_content.append("\n".join(merged_narrative))

    with open(output_file, 'w', encoding='utf-8-sig') as f:
        f.write("\n\n".join(combined_content))

if __name__ == "__main__":
    process_scripts()
