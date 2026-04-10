import re

fp = r'c:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\엔딩_HTML.txt'
with open(fp, encoding='utf-8') as f:
    text = f.read()

# Fix the triple span residue
text = text.replace('</span></span></span>', '</span></span>')

with open(fp, 'w', encoding='utf-8') as f:
    f.write(text)
print("Cleaned")
