# 게화 BGM 계획

방식은 도플로이드와 같다. 단계별 분위기를 정하고, Pixabay(상업 이용 가능, 저작자 표시 불필요)에서 맞는 음원을 골라 `audios/`에 저장한 뒤, 업로드와 DB 반영은 `murdex-bgm` 스킬의 `upload_bgm.py`로 한다.

공통 원칙
- 모든 단계 프롬프트가 "일정한 강도, 빌드업 없음, 반복 재생에 어울림"이다. 곡 중간에 고조되거나 끝이 뚝 끊기는 트랙은 피한다.
- 작품 규모는 연쇄 사망이 있는 고립 섬마을 스릴러다. 너무 가볍고 밝은 곡, 전투 서사시처럼 웅장한 곡은 피하고, 어둡고 차가운 저강도 앰비언트를 기본으로 한다.
- 보컬이 있는 곡은 쓰지 않는다.
- 단계 안내문과 대본을 읽는 시간이 길어서 음량 변화가 큰 곡은 부담이 된다.

## 단계 구성 (12단계)
시작(1), 대면(2), 1차 조사(3), 1차 추리(4), 2차 조사(5), 2차 추리(6), 3차 조사(7), 3차 추리(8), 4차 조사(9), 최종 추리(10), 최종 결론(11), 끝(12).
추리 단계(4, 6, 8, 10)는 두 사람이 전화로 통화하는 시간이라 BGM 없이 간다. 아래 표의 단계 번호는 새 번호에 맞춰 읽는다.

## 곡 배정 (7곡)

| 파일명(예정) | 적용 | 분위기 | Pixabay 검색 키워드 |
|---|---|---|---|
| 0_룸_로비.mp3 | 룸 로비 | 안개 낀 해안에 도착하기 전의 고요한 기대와 불안. 프롬프트가 없어 시작 단계 곡보다 한 단계 부드럽게 | `dark ambient sea`, `foggy coast ambient`, `mysterious calm drone` |
| 1_시작.mp3 | 1단계 시작 | 느린 아날로그 패드, 낮은 바다 드론, 멀리서 들리는 뱃고동 같은 질감. 절제된 으스스함 | `dark ambient drone`, `foghorn ambient`, `eerie ocean ambient` |
| 2_대면.mp3 | 2단계 대면 | 차갑고 축축한 해안, 드문드문 울리는 음소거된 피아노, 파도 질감 | `cold ambient piano`, `dark piano ambient`, `sparse piano mystery` |
| 3_조사_1_2차.mp3 | 3, 5단계 (1차, 2차 조사) | 부드러운 아르페지오 신스, 은은한 시계 초침 같은 타악, 약한 불협 현. 조용한 불안 | `investigation ambient`, `ticking clock tension ambient`, `x files style ambient` |
| 3_조사_3_4차.mp3 | 7, 9단계 (3차, 4차 조사) | 앞 곡과 같은 결에서 한 톤 어둡고 낮게. 진상에 가까워진다는 느낌, 단 강도는 일정하게 | `dark investigation ambient`, `suspense drone low`, `unsettling ambient pulse` |
| 11_최종_결론.mp3 | 11단계 최종 결론 | 높은 음에 머무는 긴장된 현, 낮게 맥동하는 신스 베이스, 말 없는 합창 패드. 오케스트라 하이브리드지만 전투 음악은 아니다 | `dark orchestral tension`, `cinematic suspense strings`, `dark hybrid tension` |
| 12_끝.mp3 | 12단계 끝 | 쓸쓸하고 씁쓸한 여운. 옅은 패드, 멀리서 들리는 피아노 모티프, 파도 질감. 풀리지 않은 미스터리의 정리 | `melancholic ambient ending`, `bittersweet piano ambient`, `sad ambient sea` |

조사 단계 4개를 한 곡으로 쓰지 않고 둘로 나눈 이유: 조사 단계가 총 20분이라 같은 곡이 계속 반복되면 지루하다. 사이사이에 BGM 없는 통화 단계가 끼어 있어 곡이 이어지지 않는다는 점도 있다. 두 곡은 같은 계열로 고르되 5, 6차 쪽을 약간 더 어둡게 한다.

## 선정할 때 확인할 것
- 트랙 제목만 보고 고르지 않는다. 페이지의 장르와 자유 태그를 읽고, 제목과 실제 태그가 다른 AI 생성 곡을 거른다.
- "솔로 피아노/현대 고전" 장르의 분위기 칩은 신뢰하기 어렵다. 하단 자유 태그를 우선한다.
- 에이전트는 오디오를 들을 수 없다. 후보를 고르면 사람이 직접 들어보고 확인한다. 특히 11단계(최종 결론)와 12단계(끝)는 꼭 들어볼 것.
- 길이는 2분 이상을 우선한다(반복 이음새가 덜 드러난다).

## 진행 상태
- [x] 단계별 분위기 정리
- [x] Pixabay 후보 1차 선정 (아래 후보표, 제목과 태그만 보고 고른 것이라 청취 필요)
- [x] 사용자 후보 확정 (2026-10-06, 청취 확인은 사용자가 후보 단계에서 진행)
- [ ] 다운로드, 업로드, DB 반영 (`upload_bgm.py`)
- [ ] 단계 txt의 `6. BGM`에 트랙명과 URL 기록

## 후보표 (2026-10-06, 제목과 태그 기준, 아직 듣지 않음)

| 적용 | 1순위 | 대안 |
|---|---|---|
| 룸 로비 | Underwater -mysterious ambient music (HarumachiMusic, 2:05, 신비, Ambient/Mysterious/Dark) | Coral Dreams (Cilvarium, 2:46) |
| 1단계 시작 | Forevermore (Dark Ambient) (9JackJack8, 3:10, 태그: 수중, 가라앉은, 버려진) | Deep Down (331music, 2:03, 깊은 바다) |
| 2단계 대면 | Rain Drops At Sea - Ambient Piano (Dream-Protocol, 3:49, 사운드스코어, 숙고) | |
| 3, 5단계 조사 | Mystery Detective Investigation Music (ViacheslavStarostin, 2:29, 서스펜스, 형사, 미스터리) | Investigation Piano (leberch, 2:14) |
| 7, 9단계 조사 | Tides (Suspense) (leberch, 4:00, 서스펜스, 긴장감) | Meiousal (Suspense) (leberch, 2:00), Tension Atmosphere (leberch, 2:14) |
| 11단계 최종 결론 | Dark Cinematic (leberch, 3:06, 서스펜스) | Cello's Dark Prophecy (AiCanvas, 3:42), Thriller Tension (leberch, 2:24) |
| 12단계 끝 | La Mer (Ashot_Danielyan, 9:50, 명상, 대기) | Piano of the Tides (tideblue) |

주의: leberch 곡은 "빌드업" 성격일 수 있어 11단계 외에는 앞부분만 확인할 것. "Dark Cinematic"은 같은 제목의 곡이 여러 개라 링크로 구별한다.

7단계 최종 추리용으로 골랐던 Melancholic Piano Soundtrack 등은 통화 단계(BGM 없음)로 바뀌어 쓰지 않는다. 12단계(끝) 대안으로 돌려 쓸 수 있다.

## 2026-10-06 조정 (사용자 지시)
- 3, 5단계 조사: Investigation Piano (leberch, 2:14)
- 7단계 조사: Meiousal (Suspense) (leberch, 2:00), 9단계 조사: Tension Atmosphere (leberch, 2:14)
- 12단계 끝: La Mer는 파일 용량이 커서 제외. 용량이 작은 후보로 교체 예정
  - 1순위 teardrop -calm reflective piano (HarumachiMusic, 2:41, 현대 고전, Sad/Reflective/Tranquil)
  - 대안 ambient piano "Candrika" -Moonlight- (leela_takaki, 3:10), Ocean - Ambient Synthesizer (NRA-LAB, 3:07), Underwater Dreamscape (alex-morgan, 3:42)

## 다운로드 완료 (2026-10-06, `audios/`)
| 파일 | 적용 단계 | 곡 (아티스트, Pixabay) | 크기 |
|---|---|---|---|
| 0_룸_로비.mp3 | 룸 로비 | Underwater -mysterious ambient music (HarumachiMusic) | 3.8MB |
| 1_시작.mp3 | 1 시작 | Forevermore (Dark Ambient) (9JackJack8) | 5.8MB |
| 2_대면.mp3 | 2 대면 | Rain Drops At Sea - Ambient Piano (Dream-Protocol) | 7.0MB |
| 3_5_조사_1_2차.mp3 | 3, 5 조사 | Investigation Piano (leberch) | 4.1MB |
| 7_조사_3차.mp3 | 7 조사 | Meiousal (Suspense) (leberch) | 3.7MB |
| 9_조사_4차.mp3 | 9 조사 | Tension Atmosphere (leberch) | 4.1MB |
| 11_최종_결론.mp3 | 11 최종 결론 | Dark Cinematic (leberch) | 5.7MB |
| 12_끝.mp3 | 12 끝 | teardrop -calm reflective piano (HarumachiMusic) | 4.9MB |

남은 일: Cloudinary 업로드와 DB 반영(`upload_bgm.py`), 단계 txt의 `6. BGM`에 URL 기록.
