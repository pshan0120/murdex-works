$filePath = "d:\dev\murdex-works\바스타즈 오브 더 유니버스\top-down\단서.txt"
$content = Get-Content -Path $filePath -Encoding UTF8 -Raw

# Split clue_03 logic
$oldClue03Pattern = '\[clue_03\][\s\S]*?내용 : 슬리더에게 도착한 협박 쪽지 및 마력석\. \(바스타즈에 들어오기 전, 골든 킹과 거래하고 있었다는 증거인 지령서 / 말리스가 가지고 있다면 전투력 \+8\)'
$newClues = @"
[clue_03]
이름 : 슬리더: 협박 쪽지
유형 : 물증
단계 : 역할 보유
소모AP : 0
정렬순서 : 30
중요도 : 높음
핵심 단서 여부 : Y
교환 가능 여부 : N
획득 가능 여부 : N
획득 조건 존재 여부 : N
획득 조건 내용 : 없음
시작 표시 상태 : 앞면
단계 시작시 자동 획득 : Y
관련 : 슬리더
의도 : 개인별 비밀 및 동기 부여
내용 : 슬리더에게 도착한 협박 쪽지. (바스타즈에 들어오기 전, 골든 킹과 거래하고 있었다는 증거인 지령서)

[clue_04]
이름 : 마력석
유형 : 물증
단계 : 역할 보유
소모AP : 0
정렬순서 : 40
중요도 : 높음
핵심 단서 여부 : Y
교환 가능 여부 : N
획득 가능 여부 : N
획득 조건 존재 여부 : N
획득 조건 내용 : 없음
시작 표시 상태 : 앞면
단계 시작시 자동 획득 : Y
관련 : 슬리더
의도 : 캐릭터 능력치 보정 아이템
내용 : 슬리더가 소지하고 있는 신비한 마력석. (말리스가 가지고 있다면 전투력 +8)
"@

# Split the content by the original clue_03 block
if ($content -match $oldClue03Pattern) {
    $parts = [System.Text.RegularExpressions.Regex]::Split($content, [System.Text.RegularExpressions.Regex]::Escape($Matches[0]))
    $prefix = $parts[0]
    $suffix = $parts[1]

    # Process suffix: Increment IDs and Sort Orders
    # Increment IDs [clue_XX] -> [clue_XX+1]
    # We must do this from largest to smallest to avoid double incrementing if using simple string replace,
    # but here we use regex which matches all instances once.
    
    $incrementedSuffix = [re]::Replace($suffix, '\[clue_(\d+)\]', {
        param($m)
        $id = [int]$m.Groups[1].Value
        return "[clue_$(" + ($id + 1).ToString("00") + ")]"
    })

    $incrementedSuffix = [re]::Replace($incrementedSuffix, '정렬순서 : (\d+)', {
        param($m)
        $order = [int]$m.Groups[1].Value
        return "정렬순서 : $($order + 10)"
    })

    $finalContent = $prefix + $newClues + $incrementedSuffix
    Set-Content -Path $filePath -Value $finalContent -Encoding UTF8
    Write-Host "Update successful."
} else {
    Write-Error "Original clue_03 block not found."
}
