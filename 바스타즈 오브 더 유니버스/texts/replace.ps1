$files = Get-ChildItem '*.txt'
foreach ($f in $files) {
    $content = [System.IO.File]::ReadAllText($f.FullName)
    if ($content -match '<span class="character-bastards">바스타즈</span>') {
        $content = $content.Replace('<span class="character-bastards">바스타즈</span>', '<span class="character-bastards">바스타즈</span>')
        [System.IO.File]::WriteAllText($f.FullName, $content, [System.Text.Encoding]::UTF8)
        Write-Output "Updated $($f.Name)"
    }
}
