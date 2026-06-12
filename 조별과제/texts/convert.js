const fs = require('fs');
const files = [
  'c:/dev/KLIEN/murdex/works/조별과제/texts/역할정보_이준서.txt',
  'c:/dev/KLIEN/murdex/works/조별과제/texts/역할정보_최도윤.txt',
  'c:/dev/KLIEN/murdex/works/조별과제/texts/역할정보_한세린.txt',
  'c:/dev/KLIEN/murdex/works/조별과제/texts/역할정보_황기순.txt'
];

for (const file of files) {
  let content = fs.readFileSync(file, 'utf8');
  let original = content;

  // 1. replace standard details block
  content = content.replace(/<details(?: open)?>[\s\S]*?<summary>\s*([^<]+)\s*<span class="toggle-wrapper">[\s\S]*?<\/summary>\s*<div class="collapsible-content">/g, (match, title) => {
    return `<div class="section-title">${title.trim()}</div>`;
  });

  // 2. replace summary-header details block
  content = content.replace(/<details(?: open)?>[\s\S]*?<summary class="summary-header">\s*(<span[^>]+>[^<]+<\/span>)[\s\S]*?<\/summary>\s*<div class="collapsible-content">/g, (match, span) => {
    return `<div class="subsection-title">${span.trim()}</div>`;
  });

  // 3. remove the closing tags for collapsible-content and details
  content = content.replace(/<\/div>\s*<\/details>/g, '');

  fs.writeFileSync(file, content, 'utf8');
  console.log(file + ' updated. original length: ' + original.length + ' new length: ' + content.length);
}
