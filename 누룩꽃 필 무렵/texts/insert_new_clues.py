import pymysql
import os
import uuid
import re
from dotenv import load_dotenv

load_dotenv(r"c:\dev\KLIEN\murdex\murdex-api\.env")

STORY_ID = "11ac5811-9d96-4756-ad87-7d18764662ce"

def parse_clues(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    clues = []
    # Pattern to match the 12 new clues: clue_p_{name}_00_{who|dark}
    pattern = r'### \[clue_p_[a-z]+_00_(?:who|dark)\]\s+이름 : (.*?)\n유형 : (.*?)\n단계 : (.*?)\n소모AP : (.*?)\n정렬순서 : (.*?)\n중요도 : (.*?)\n핵심 단서 여부 : (.*?)\n교환 가능 여부 : (.*?)\n획득 가능 여부 : (.*?)\n획득 조건 존재 여부 : (.*?)\n획득 조건 내용 : (.*?)\n시작 표시 상태 : (.*?)\n단계 시작시 자동 획득 : (.*?)\n관련 : (.*?)\n의도 : (.*?)\n내용 :\n(.*?)\nHTML :\n(.*?)(?=\n### \[clue|$)'
    
    matches = re.finditer(pattern, content, re.DOTALL)
    for match in matches:
        clue_name = match.group(1).strip()
        clue_type_str = match.group(2).strip()
        ap_cost = int(match.group(4).strip())
        clue_order = int(match.group(5).strip())
        importance_str = match.group(6).strip()
        can_exchange = 1 if match.group(8).strip() == 'Y' else 0
        can_acquire = 1 if match.group(9).strip() == 'Y' else 0
        has_condition = 1 if match.group(10).strip() == 'Y' else 0
        condition_text = match.group(11).strip()
        if condition_text == '없음':
            condition_text = None
            
        html_content = match.group(17).strip()
        
        # map type
        type_map = {
            '물증': 'PHYSICAL',
            '증언': 'TESTIMONY',
            '관계': 'RELATIONSHIP',
            '타임라인': 'TIMELINE',
            '관찰': 'OBSERVATION',
            '통찰': 'INSIGHT'
        }
        clue_type = type_map.get(clue_type_str, 'INSIGHT')
        
        # map importance
        imp_map = {
            '높음': 'HIGH',
            '보통': 'MEDIUM',
            '낮음': 'LOW'
        }
        importance_level = imp_map.get(importance_str, 'MEDIUM')

        clues.append({
            'clue_name': clue_name,
            'clue_type': clue_type,
            'importance_level': importance_level,
            'ap_cost': ap_cost,
            'clue_order': clue_order,
            'is_exchangeable': can_exchange,
            'is_acquirable': can_acquire,
            'has_acquisition_condition': has_condition,
            'acquisition_condition': condition_text,
            'html_content': html_content
        })
    return clues

def insert_clues(clues):
    conn = pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT")),
        database=os.getenv("MYSQL_DATABASE"),
        user=os.getenv("MYSQL_USERNAME"),
        password=os.getenv("MYSQL_PASSWORD")
    )
    cursor = conn.cursor()
    
    inserted_count = 0
    try:
        for clue in clues:
            clue_id = str(uuid.uuid4())
            variant_id = str(uuid.uuid4())
            
            # Insert into clue
            sql_clue = """
            INSERT INTO clue (
                clue_id, story_id, clue_type, importance_level, is_revealable,
                is_exchangeable, ap_cost, clue_order, is_acquirable,
                is_disposable_read, has_acquisition_condition, acquisition_condition
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_clue, (
                clue_id, STORY_ID, clue['clue_type'], clue['importance_level'], 0,
                clue['is_exchangeable'], clue['ap_cost'], clue['clue_order'], clue['is_acquirable'],
                0, clue['has_acquisition_condition'], clue['acquisition_condition']
            ))
            
            # Insert into clue_variant
            sql_variant = """
            INSERT INTO clue_variant (
                variant_id, clue_id, clue_name, variant_type, clue_content,
                is_default, priority
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_variant, (
                variant_id, clue_id, clue['clue_name'], 'DEFAULT', clue['html_content'],
                1, 0
            ))
            
            inserted_count += 1
            print(f"Inserted: {clue['clue_name']} (Order: {clue['clue_order']})")
            
        conn.commit()
        print(f"Successfully inserted {inserted_count} clues.")
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    clues_file = r"c:\dev\KLIEN\murdex\works\누룩꽃 필 무렵\texts\단서.txt"
    clues = parse_clues(clues_file)
    print(f"Found {len(clues)} new clues to insert.")
    if len(clues) == 12:
        insert_clues(clues)
    else:
        print("Expected exactly 12 clues, found a different number. Please check regex.")
