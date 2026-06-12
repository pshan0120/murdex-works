const fs = require('fs');
const file = 'c:/dev/KLIEN/murdex/works/바스타즈 오브 더 유니버스/texts/역할_1_스컬크러셔.txt';

let content = fs.readFileSync(file, 'utf8');
let originalContent = content;

// Since story-content wraps almost everything, we can just find where it starts and ends
// But there are two story-content blocks in this file!
// Let's do it by index.
let pos = 0;
while ((pos = content.indexOf('<div class="story-content">', pos)) !== -1) {
  const startContent = pos + '<div class="story-content">'.length;
  
  // Find the matching closing </div> for this story-content
  let depth = 1;
  let curr = startContent;
  while (depth > 0 && curr < content.length) {
    const nextDiv = content.indexOf('<div', curr);
    const nextClose = content.indexOf('</div>', curr);
    
    if (nextClose === -1) break; // Error
    
    if (nextDiv !== -1 && nextDiv < nextClose) {
      depth++;
      curr = nextDiv + 4;
    } else {
      depth--;
      curr = nextClose + 6;
    }
  }
  
  const endContent = curr - 6; // before the closing </div>
  const inside = content.substring(startContent, endContent);
  
  // split inside by <div class="section-title">
  // but only if it contains section-title
  if (inside.includes('<div class="section-title">')) {
    const sections = inside.split(/(?=<div class="section-title">)/g);
    const newInside = sections.map(s => {
      if (!s.trim()) return s;
      return `\n<section class="content-section">\n${s.trim()}\n</section>\n`;
    }).join('');
    
    content = content.substring(0, startContent) + newInside + content.substring(endContent);
    // adjust pos to continue searching
    pos = startContent + newInside.length + 6;
  } else {
    // skip this one
    pos = endContent + 6;
  }
}

fs.writeFileSync(file, content, 'utf8');
console.log('Done!');
