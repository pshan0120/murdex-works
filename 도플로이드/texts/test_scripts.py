import re
import os
import sys

def parse_lines(file_path):
    """
    대본 파일에서 캐릭터 라벨과 대사 내용을 파싱합니다.
    """
    if not os.path.exists(file_path):
        return []

    pattern = re.compile(
        r'<div class="script-line (?:my-line|other-character)">\s*<span class="script-character(?: my-character)?">(.*?)</span>:\s*"(.*?)"\s*</div>',
        re.DOTALL
    )
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return pattern.findall(content)

def check_script_alignment(narrative_idx, lines_a, lines_c):
    """
    A 대본과 C 대본의 줄 수 및 화자 정합성을 검증합니다.
    """
    errors = []
    
    # 1. 줄 수 비교
    if len(lines_a) != len(lines_c):
        errors.append(f"줄 수 불일치: A={len(lines_a)}, C={len(lines_c)}")
        return errors # 조기 반환 (보호절)

    is_odd = (narrative_idx % 2 != 0)

    for idx, (a_turn, c_turn) in enumerate(zip(lines_a, lines_c)):
        char_a, text_a = a_turn
        char_c, text_c = c_turn

        # 홀수 단계: A 먼저 시작 (idx 0, 2, 4.. 는 A 차례 / 1, 3, 5.. 는 C 차례)
        # 짝수 단계: C 먼저 시작 (idx 0, 2, 4.. 는 C 차례 / 1, 3, 5.. 는 A 차례)
        is_a_turn = (idx % 2 == 0) if is_odd else (idx % 2 != 0)

        if is_a_turn:
            # A가 말하는 차례
            if 'A' not in char_a and '레바' not in char_a:
                errors.append(f"[{idx}] A 차례 오류: A파일 라벨 '{char_a}'")
            if 'A' not in char_c and '레바' not in char_c:
                errors.append(f"[{idx}] A 차례 오류: C파일 라벨 '{char_c}'")
        else:
            # C가 말하는 차례
            if 'C' not in char_a and '니악' not in char_a:
                errors.append(f"[{idx}] C 차례 오류: A파일 라벨 '{char_a}'")
            if 'C' not in char_c and '니악' not in char_c:
                errors.append(f"[{idx}] C 차례 오류: C파일 라벨 '{char_c}'")

        # placeholder 텍스트 뒷부분 매칭 체크 (느슨하게 단어 끝 4글자 매칭)
        clean_text_a = text_a.replace('&nbsp;', '').strip()
        clean_text_c = text_c.replace('&nbsp;', '').strip()

        if is_a_turn:
            # A가 실제 대사를 쳤고 C 대본의 text_c는 placeholder임
            match_suffix = clean_text_c[-4:] if len(clean_text_c) >= 4 else clean_text_c
            if match_suffix not in clean_text_a:
                errors.append(f"[{idx}] 텍스트 정합성 오류: C파일 placeholder '{clean_text_c}'가 A파일 실제대사 '{clean_text_a}'와 미매칭")
        else:
            # C가 실제 대사를 쳤고 A 대본의 text_a는 placeholder임
            match_suffix = clean_text_a[-4:] if len(clean_text_a) >= 4 else clean_text_a
            if match_suffix not in clean_text_c:
                errors.append(f"[{idx}] 텍스트 정합성 오류: A파일 placeholder '{clean_text_a}'가 C파일 실제대사 '{clean_text_c}'와 미매칭")

    return errors

def verify_guide_text(narrative_idx, file_path_a, file_path_c):
    """
    각 대본 파일 상단의 가이드 텍스트가 시작 화자 설계와 일치하는지 확인합니다.
    """
    errors = []
    if not os.path.exists(file_path_a) or not os.path.exists(file_path_c):
        return errors # 보호절

    with open(file_path_a, 'r', encoding='utf-8') as f:
        content_a = f.read()
    with open(file_path_c, 'r', encoding='utf-8') as f:
        content_c = f.read()

    is_odd = (narrative_idx % 2 != 0)
    
    # 홀수: A 대본(당신(A)부터 시작), C 대본(상대방(A)부터 시작)
    # 짝수: A 대본(상대방(C)부터 시작), C 대본(당신(C)부터 시작)
    expected_guide_a = "당신(A)부터 시작합니다." if is_odd else "상대방(C)부터 시작합니다."
    expected_guide_c = "상대방(A)부터 시작합니다." if is_odd else "당신(C)부터 시작합니다."

    if expected_guide_a not in content_a:
        errors.append(f"A 파일 가이드 텍스트 불일치: 기대값 '{expected_guide_a}'")
    if expected_guide_c not in content_c:
        errors.append(f"C 파일 가이드 텍스트 불일치: 기대값 '{expected_guide_c}'")

    return errors

def run_tests():
    # Windows cp949 인코딩으로 인한 sys.stdout 인코딩 강제 재정의
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

    base_path = r'c:\dev\KLIEN\murdex\works\도플로이드\texts'
    all_success = True
    
    print("=== 도플로이드 대본 정합성 단위 테스트 시작 ===")
    
    for i in range(1, 12):
        file_a = os.path.join(base_path, f'대본_서사{i}_A.txt')
        file_c = os.path.join(base_path, f'대본_서사{i}_C.txt')
        
        if not os.path.exists(file_a) or not os.path.exists(file_c):
            print(f"[서사 {i}] 파일 누락 - 건너뜀")
            continue
            
        lines_a = parse_lines(file_a)
        lines_b = parse_lines(file_c)
        
        align_errors = check_script_alignment(i, lines_a, lines_b)
        guide_errors = verify_guide_text(i, file_a, file_c)
        
        total_errors = align_errors + guide_errors
        
        if total_errors:
            print(f"[FAIL] [서사 {i}] 테스트 실패!")
            for err in total_errors:
                print(f"   - {err}")
            all_success = False
        else:
            print(f"[PASS] [서사 {i}] 테스트 통과 (대사 {len(lines_a)}개)")
            
    print("===============================================")
    if all_success:
        print("[SUCCESS] 모든 대본 정합성 테스트 통과!")
        return 0
    else:
        print("[ERROR] 일부 대본 정합성 테스트 실패. 대본 파일을 수정해 주세요.")
        return 1

if __name__ == '__main__':
    sys.exit(run_tests())
