$files = @(
    "역할_고어후프_분리.txt",
    "역할_말리스_분리.txt",
    "역할_발로그_분리.txt",
    "역할_발트라_분리.txt",
    "역할_스컬크러셔_분리.txt",
    "역할_슬리더_분리.txt",
    "역할_엘드리치_분리.txt"
)

$basePath = "c:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts"

foreach ($file in $files) {
    $path = Join-Path $basePath $file
    if (Test-Path $path) {
        $content = Get-Content -Path $path -Raw -Encoding UTF8
        # Regex to find <span class="emphasis">'...'</span> and remove the single quotes
        $newContent = [regex]::Replace($content, '<span class="emphasis">''(.*?)''</span>', '<span class="emphasis">$1</span>')
        Set-Content -Path $path -Value $newContent -Encoding UTF8
        Write-Host "Updated $file"
    } else {
        Write-Host "File not found: $path"
    }
}
