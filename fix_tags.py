import os
import re

texts_dir = 'c:\\dev\\KLIEN\\murdex\\works\\도플로이드\\texts'
for filename in os.listdir(texts_dir):
    if filename.endswith('.txt'):
        path = os.path.join(texts_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix </strong\n>:
        content = re.sub(r'</strong\s*>\s*:', '</strong>:', content)
        
        # Fix <span class=\n"..."\n>
        content = re.sub(r'<span class=[\r\n\s]+', '<span class=', content)
        content = re.sub(r'class=\"([^\"]+)\"[\r\n\s]+>', r'class="\1">', content)
        
        # Fix </span\n>
        content = re.sub(r'</span\s*>', '</span>', content)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
print("Tags fixed.")
