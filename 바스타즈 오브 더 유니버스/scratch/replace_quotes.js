const fs = require('fs');

const baseDir = 'c:\\dev\\KLIEN\\murdex\\works\\바스타즈 오브 더 유니버스\\texts';

const filePaths = [
    '역할_말리스_분리.txt',
    '역할_고어후프_분리.txt',
    '역할_발로그_분리.txt',
    '역할_발트라_분리.txt',
    '역할_스컬크러셔_분리.txt',
    '역할_슬리더_분리.txt',
    '역할_엘드리치_분리.txt',
].map(name => `${baseDir}\\${name}`);

let hasError = false;

filePaths.forEach(filePath => {
    try {
        if (!fs.existsSync(filePath)) {
            console.error('File not found:', filePath);
            hasError = true;
            return;
        }

        const content = fs.readFileSync(filePath, 'utf8');
        // HTML 태그(<...>) 경계로 분할하여 태그 외부의 쌍따옴표만 교체
        const parts = content.split(/(<[^>]+>)/g);
        const result = parts.map(part => {
            if (part.startsWith('<')) {
                return part; // HTML 태그 내부는 그대로 유지
            }
            return part.replace(/"/g, '&quot;');
        }).join('');

        fs.writeFileSync(filePath, result, 'utf8');
        console.log(`✅ Done: ${filePath.split('\\').pop()}`);
    } catch (err) {
        console.error(`❌ Error in ${filePath.split('\\').pop()}:`, err.message);
        hasError = true;
    }
});

if (hasError) {
    process.exit(1);
} else {
    console.log('\n모든 파일 처리가 완료되었습니다.');
}
