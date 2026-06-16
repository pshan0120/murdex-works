import sys

file_path = r'c:\dev\KLIEN\murdex\works\조별과제\texts\단계정보_대본1.txt'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix double wrapped script characters
content = content.replace('<span class=\"script-character character-lee\"><span class=\"character-lee\">이준서</span></span>', '<span class=\"script-character character-lee\">이준서</span>')
content = content.replace('<span class=\"script-character character-han\"><span class=\"character-han\">한세린</span></span>', '<span class=\"script-character character-han\">한세린</span>')
content = content.replace('<span class=\"script-character character-choi\"><span class=\"character-choi\">최도윤</span></span>', '<span class=\"script-character character-choi\">최도윤</span>')
content = content.replace('<span class=\"script-character character-hwang\"><span class=\"character-hwang\">황기순</span></span>', '<span class=\"script-character character-hwang\">황기순</span>')

# Fix other accidental double wraps like <span class="character-lee"><span class="character-lee">이준서</span></span>
content = content.replace('<span class=\"character-lee\"><span class=\"character-lee\">이준서</span></span>', '<span class=\"character-lee\">이준서</span>')
content = content.replace('<span class=\"character-han\"><span class=\"character-han\">한세린</span></span>', '<span class=\"character-han\">한세린</span>')
content = content.replace('<span class=\"character-choi\"><span class=\"character-choi\">최도윤</span></span>', '<span class=\"character-choi\">최도윤</span>')
content = content.replace('<span class=\"character-hwang\"><span class=\"character-hwang\">황기순</span></span>', '<span class=\"character-hwang\">황기순</span>')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed!')
