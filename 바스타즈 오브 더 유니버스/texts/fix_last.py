import sys, json, re
sys.stdout.reconfigure(encoding='utf-8')

with open('dump_bastards_clues.json', 'r', encoding='utf-8') as f:
    clues = {c['clue_name']: c for c in json.load(f)}

with open('단서.txt', 'r', encoding='utf-8') as f:
    content = f.read()

def replace_block(name, db_name):
    global content
    if db_name not in clues: return
    c = clues[db_name]
    
    clue_id = c['clue_id']
    variant_id = c['variant_id']
    
    pattern = r'(이름 : ' + re.escape(name) + r'\n)(?:예전 이름 : .*\n)?(?:clue_id : .*\n)?(?:variant_id : .*\n)?'
    repl = f'\\g<1>예전 이름 : {db_name}\nclue_id : {clue_id}\nvariant_id : {variant_id}\n'
    content = re.sub(pattern, repl, content)
    print(f"Fixed {name}")

replace_block('식당#1 (비밀금고)', '식당#1')
replace_block('문서고#4 (비밀서고)', '문서고#6')
replace_block('문서고#5 (책상)', '문서고#5')

with open('단서.txt', 'w', encoding='utf-8') as f:
    f.write(content)
