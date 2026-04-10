$file = 'ending_html.txt'
Copy-Item '엔딩_HTML.txt' $file

$content = [System.IO.File]::ReadAllText((Join-Path (Get-Location) $file), [System.Text.Encoding]::UTF8)

# map: display name -> css class
$pairs = @(
    @('마신 다크 시리어스', 'mystery'),
    @('류크(스컬크러셔)', 'character-skullcrusher'),
    @('스컬크러셔', 'character-skullcrusher'),
    @('말리스', 'character-malice'),
    @('발로그', 'character-balrog'),
    @('발트라', 'character-valtra'),
    @('고어후프', 'character-gorehoof'),
    @('슬리더', 'character-slither'),
    @('엘드리치', 'character-eldritch'),
    @('다크 시리어스', 'mystery')
)

foreach ($pair in $pairs) {
    $name = $pair[0]
    $cls  = $pair[1]
    $escaped = [System.Text.RegularExpressions.Regex]::Escape($name)
    $pattern = '(<span class="script-character">)(' + $escaped + ')(</span>)'
    $repl    = '$1<span class="' + $cls + '">$2</span>$3'
    $content = [System.Text.RegularExpressions.Regex]::Replace($content, $pattern, $repl)
}

[System.IO.File]::WriteAllText((Join-Path (Get-Location) $file), $content, [System.Text.Encoding]::UTF8)
Copy-Item $file '엔딩_HTML.txt' -Force
Remove-Item $file
Write-Host 'Done'
