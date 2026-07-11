import sys

diff_file = 'c:/dev/KLIEN/murdex/works/누룩꽃 필 무렵/texts/박사_작가_변경내역.diff'
with open(diff_file, 'r', encoding='utf-16') as f:
    lines = f.readlines()

current_file = ''
changes = {}

for line in lines:
    if line.startswith('+++ b/'):
        current_file = line[6:].strip()
        changes[current_file] = []
    elif line.startswith('-') and not line.startswith('---'):
        changes[current_file].append({'old': line[1:].strip(), 'new': ''})
    elif line.startswith('+') and not line.startswith('+++'):
        if len(changes[current_file]) > 0 and changes[current_file][-1]['new'] == '':
            changes[current_file][-1]['new'] = line[1:].strip()

out = []
for f, f_changes in changes.items():
    if not f_changes: continue
    out.append(f"## {f}\n")
    for c in f_changes:
        if c['old']:
            out.append("- **수정 전**: " + c['old'])
            out.append("  **수정 후**: " + c['new'] + "\n")

with open('c:/dev/KLIEN/murdex/works/누룩꽃 필 무렵/texts/변경요약.md', 'w', encoding='utf-8') as out_f:
    out_f.write('\n'.join(out))
print("Summary generated")
