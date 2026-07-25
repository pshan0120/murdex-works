import sys
import os
import re
import argparse
import subprocess
from bs4 import BeautifulSoup, NavigableString, Tag

sys.stdout.reconfigure(encoding='utf-8')

def load_keywords(work_dir):
    """
    작품 폴더 내 CSS 및 텍스트 파일들을 기반으로 키워드와 CSS 클래스 매핑을 생성합니다.
    """
    char_map = [
        ("닥터 클레이", "character-clay"),
        ("소장 클레이", "character-clay"),
        ("클레이", "character-clay"),
        ("베일라", "character-veyla"),
        ("마커스", "character-marcus"),
        ("알렉스", "character-alex"),
        ("AIex", "character-alex"),
    ]
    
    emphasis_terms = set([
        "도플로이드", "프로메테우스 연구소", "프로메테우스",
        "정문 로비", "보안 검색대", "소장실", "일반 연구실",
        "비밀 병실", "보안 물품 창고", "서쪽 환풍구", "서쪽 환기구",
        "기록 보관실", "폐기물 소각장", "지하 배양실", "배양실", "주 배양실"
    ])
    
    # 단서_그룹.txt에서 그룹명 추가 수집
    group_file = os.path.join(work_dir, "texts", "단서_그룹.txt")
    if os.path.exists(group_file):
        with open(group_file, "r", encoding="utf-8") as f:
            text = f.read()
        matches = re.findall(r'\d+\.\s+(.*?)\n', text)
        for m in matches:
            clean_m = re.sub(r'\(.*?\)', '', m).strip()
            if clean_m:
                emphasis_terms.add(clean_m)
                
    # Sort char_map by keyword length descending to match longest phrases first
    char_map.sort(key=lambda x: len(x[0]), reverse=True)
    
    emp_list = [(term, "emphasis") for term in sorted(list(emphasis_terms), key=lambda x: len(x), reverse=True)]
    
    # Combined rules
    all_rules = char_map + emp_list
    return all_rules

def decorate_html_content(html_str, rules):
    """
    HTML 문자열 내의 텍스트 노드에서 키워드를 찾아 <span> 태그로 감쌉니다.
    이미 <span>으로 감싸져 있는 키워드는 재감싸기 하지 않습니다.
    """
    soup = BeautifulSoup(html_str, 'html.parser')
    
    # Find all text nodes that are not inside a script, style, or already inside span.character-*/span.emphasis
    def process_node(node):
        if isinstance(node, NavigableString):
            parent = node.parent
            if parent and parent.name in ['script', 'style']:
                return
            if parent and parent.name == 'span' and ('character-' in parent.get('class', [''])[0] or 'emphasis' in parent.get('class', [''])[0]):
                return
                
            text = str(node)
            modified = False
            
            # Apply rules
            for keyword, cls_name in rules:
                # Regex to find keyword NOT inside html tag/attribute
                # If keyword is already inside <span>, ignore
                if keyword in text:
                    # Pattern matching keyword when not surrounded by span tags
                    pattern = re.compile(rf'(?<!<span class="{cls_name}">){re.escape(keyword)}(?!</span>)')
                    if pattern.search(text):
                        # Construct replacement HTML string
                        replacement = f'<span class="{cls_name}">{keyword}</span>'
                        text = pattern.sub(replacement, text)
                        modified = True
                        
            if modified:
                new_fragment = BeautifulSoup(text, 'html.parser')
                node.replace_with(new_fragment)
                
        elif isinstance(node, Tag):
            # Do not traverse into existing character or emphasis spans
            classes = node.get('class', [])
            if any(c.startswith('character-') or c == 'emphasis' for c in classes):
                return
            for child in list(node.children):
                process_node(child)
                
    for child in list(soup.children):
        process_node(child)
        
    return str(soup)

def process_file(file_path, dry_run=False):
    # Find work dir (directory containing texts or parent of texts)
    abs_path = os.path.abspath(file_path)
    dir_path = os.path.dirname(abs_path)
    
    work_dir = dir_path
    while work_dir and os.path.basename(work_dir) != "works" and os.path.basename(work_dir) != "murdex":
        if os.path.exists(os.path.join(work_dir, "styles")) or os.path.exists(os.path.join(work_dir, "texts")):
            break
        parent = os.path.dirname(work_dir)
        if parent == work_dir:
            break
        work_dir = parent
        
    rules = load_keywords(work_dir)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="cp949", errors="ignore") as f:
                lines = f.readlines()
        
    updated_lines = []
    in_html = False
    html_lines = []
    html_depth = 0
    modified_count = 0
    
    for i, line in enumerate(lines):
        if line.strip().startswith("<div class=\"story-content\"") or line.strip() == "HTML :":
            if in_html and html_lines:
                full_html = "".join(html_lines)
                decorated_html = decorate_html_content(full_html, rules)
                if decorated_html != full_html:
                    modified_count += 1
                updated_lines.append(decorated_html)
                html_lines = []
                
            in_html = True
            html_depth = line.count("<div") - line.count("</div>")
            html_lines = [line] if line.strip().startswith("<div class=\"story-content\"") else []
            if line.strip() == "HTML :":
                updated_lines.append(line)
            continue
            
        if in_html:
            html_lines.append(line)
            html_depth += line.count("<div") - line.count("</div>")
            if html_depth <= 0 or re.match(r'^\d+\.\s+', line.strip()) or (line.startswith("[") and "]" in line) or line.startswith("<!--") or line.startswith("이미지생성용 프롬프트") or line.startswith("단서 그룹 :") or line.startswith("파일명 :"):
                in_html = False
                full_html = "".join(html_lines)
                decorated_html = decorate_html_content(full_html, rules)
                if decorated_html != full_html:
                    modified_count += 1
                updated_lines.append(decorated_html)
                html_lines = []
        else:
            updated_lines.append(line)
            
    if in_html and html_lines:
        full_html = "".join(html_lines)
        decorated_html = decorate_html_content(full_html, rules)
        if decorated_html != full_html:
            modified_count += 1
        updated_lines.append(decorated_html)
        
    if not dry_run and modified_count > 0:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(updated_lines)
            
        # Call format-txt-html skill script to fix whitespace flatening caused by BeautifulSoup
        format_script_path = os.path.join(os.path.dirname(__file__), "..", "..", "format-txt-html", "scripts", "format_html.py")
        if os.path.exists(format_script_path):
            try:
                subprocess.run([sys.executable, format_script_path, file_path], check=True, capture_output=True)
                print(f"  -> Automatically formatted HTML spacing for {os.path.basename(file_path)}")
            except subprocess.CalledProcessError as e:
                print(f"  -> [WARNING] Auto-formatting failed: {e}")
                
    print(f"Processed {os.path.basename(file_path)}: decorated {modified_count} HTML blocks.")
    return modified_count

def main():
    parser = argparse.ArgumentParser(description="Decorate character names and keywords with CSS span tags in text files.")
    parser.add_argument("target_path", help="Path to text file or folder containing text files")
    parser.add_argument("--dry-run", action="store_true", help="Do not write changes to file")
    args = parser.parse_args()
    
    target = os.path.abspath(args.target_path)
    if os.path.isfile(target):
        process_file(target, dry_run=args.dry_run)
    elif os.path.isdir(target):
        count = 0
        for root, dirs, files in os.walk(target):
            for file in files:
                if file.endswith(".txt"):
                    f_path = os.path.join(root, file)
                    count += process_file(f_path, dry_run=args.dry_run)
        print(f"Total processed files decorated: {count}")

if __name__ == "__main__":
    main()
