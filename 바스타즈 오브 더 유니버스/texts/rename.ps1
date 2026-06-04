$path = "c:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts"
Get-ChildItem -Path $path -Filter "*.txt" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw -Encoding UTF8
    if ($content -match '발트라') {
        $content = $content -replace '발트라', '엘란트라'
        Set-Content -Path $_.FullName -Value $content -NoNewline -Encoding UTF8
    }
}
Rename-Item -Path "$path\역할_발트라.txt" -NewName "역할_엘란트라.txt" -ErrorAction SilentlyContinue
Rename-Item -Path "$path\역할_발트라_backup.txt" -NewName "역할_엘란트라_backup.txt" -ErrorAction SilentlyContinue
echo "Bulk replace completed."
