# crawl-blog — 프로젝트 기획서

## 서비스 개요
키워드/URL을 입력받아 Claude API가 판단 후 자동 크롤링하고,
수집된 정보를 블로그 형태로 누적 제공하는 개인용 + 포폴용 사이트.

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| 프론트 | Next.js 15 (App Router) + TypeScript + Tailwind CSS + Framer Motion |
| 백엔드 | FastAPI (Python) |
| AI | Claude API (판단 + 콘텐츠 정제) |
| 크롤링 | Playwright + BeautifulSoup |
| 스케줄링 | APScheduler |
| DB | SQLite |
| 배포 | Docker + gateway_nginx + GitHub Actions |

---

## 핵심 흐름

```
사용자 입력 (키워드 or URL + 비밀번호)
→ FastAPI 비밀번호 검증
→ Claude API 판단
  → 가능: 크롤링 대상 사이트 추천 + 등록
  → 불가능: 이유 반환 → 리스트에 표기
→ APScheduler가 주기적으로 크롤링 실행
→ 수집 내용 Claude API로 정제
→ SQLite 저장
→ Next.js 블로그 형태로 렌더링
```

---

## 기능 상세

### 1. 인풋 관리 (입력 + 리스트)

- 인풋 입력: 키워드 or URL + 비밀번호
- 하나 이상의 인풋 동시 관리 가능
- 리스트 표시 항목:
  - 인풋값
  - 상태: `활성` / `크롤링 중` / `실패` / `불가` / `삭제됨`
  - Claude 판단 결과 (가/부)
  - 부결 시 이유 표기
  - 가결 시 크롤링 방식 간단 표시
  - 마지막 크롤링 시간
  - 다음 크롤링 예정 시간
  - 수집된 글 수
  - NEW 뱃지 (새 글 수집 시)
- 삭제 기능: 삭제 시 스케줄링에서 즉시 제외
- 크롤링 주기 설정: 인풋마다 개별 설정 (1시간 / 6시간 / 매일)

### 2. Claude API 판단

- 입력값을 Claude가 분석:
  - 크롤링 가능한 사이트인지
  - 적합한 크롤링 대상 사이트 추천
  - 수집 방식 결정 (RSS / HTML 파싱 / 검색 결과 등)
- 판단 과정 실시간 스트리밍 표시 (타이핑 효과)
- 부결 이유 명확하게 리스트에 표기

### 3. 크롤링 + 정제

- Playwright로 JS 렌더링 사이트 대응
- 수집 내용 Claude API로 정제:
  - 핵심 내용 요약
  - 블로그 형태로 재구성
  - 태그 자동 추출
- 크롤링 → 정제 → 저장 과정 진행바로 시각화

### 4. 결과물 (블로그)

- 수집된 글 누적 표시
- 최신순 / 인풋별 탭 분리
- 읽음 / 안읽음 처리
- NEW 뱃지
- 글 내용 검색
- 인풋별 필터링

### 5. 보안

- bcrypt 해싱된 비밀번호 검증
- 5회 실패 시 IP 잠금 (rate limiting)
- Claude API 일일 호출 한도 설정 (캡 설정으로 과금 방지)
- 인풋 등록/삭제/수동 크롤링 트리거 → 비밀번호 필요
- 블로그 결과물 조회 → 공개
- API 엔드포인트 rate limiting
- 크롤링 대상 도메인 블랙리스트 적용
- HTTPS 필수 (gateway_nginx SSL)

---

### 6. 시스템 상태 알림 영역

항상 노출되는 상태 패널 (상단 또는 고정 영역):

- 전체 시스템 상태: `정상` / `경고` / `중단`
- 항목별 상태 표시:
  - 활성 인풋 수 (크롤링 대상)
  - Claude API 사용 가능 여부 + 잔여 한도 경고
  - 스케줄러 실행 상태 (동작 중 / 중단)
  - 마지막 크롤링 성공 시간
- 중단 원인 표시:
  - 인풋 없음
  - Claude API 한도 초과 또는 오류
  - 크롤링 연속 실패
- 상태 변경 시 애니메이션 전환 (색상 + 아이콘)

---

## 디자인 원칙

- 테이블 형태 올드한 느낌 금지
- 애니메이션 최대한 활용 (단, 60fps 유지, 느리지 않게)
  - 페이지 진입 stagger fade-in
  - 리스트 아이템 추가/삭제 애니메이션
  - 상태 변경 시 색상 전환 애니메이션
  - 글 카드 hover 효과
  - Claude 판단 과정 타이핑 스트리밍
  - 크롤링 진행 시각화 (진행바 + 단계 표시)
- 텍스트 명확하게 (높은 contrast)
- 폰트 사이즈 약간 크게 (텍스트 많은 영역 고려)
- CSS transform/opacity만 사용 (layout reflow 금지)
- 모바일 반응형

---

## 디렉토리 구조 (제안)

```
crawl-blog/
├── frontend/          # Next.js 15
│   └── src/
│       ├── app/
│       │   ├── page.tsx          # 블로그 메인 (글 목록)
│       │   ├── manage/page.tsx   # 인풋 관리
│       │   └── posts/[id]/       # 글 상세
│       └── components/
├── backend/           # FastAPI
│   ├── main.py
│   ├── crawler.py     # Playwright 크롤링
│   ├── scheduler.py   # APScheduler
│   ├── claude.py      # Claude API 연동
│   └── database.py    # SQLite
├── docker-compose.crawl-blog.yml
├── .github/workflows/deploy.yml
└── PROJECT.md
```

---

## API 엔드포인트 (FastAPI)

```
POST /api/inputs          — 인풋 등록 (비밀번호 검증 + Claude 판단)
GET  /api/inputs          — 인풋 목록 조회
DELETE /api/inputs/{id}   — 인풋 삭제 (스케줄링 제외)
PATCH /api/inputs/{id}    — 주기 변경

GET  /api/posts           — 글 목록 (필터/검색/페이지네이션)
GET  /api/posts/{id}      — 글 상세
PATCH /api/posts/{id}/read — 읽음 처리

GET  /api/status          — 크롤링 상태 실시간 조회
POST /api/crawl/{id}      — 수동 크롤링 트리거

GET  /api/claude/stream   — Claude 판단 과정 스트리밍 (SSE)
```

---

## 개발 마일스톤

| 단계 | 내용 |
|------|------|
| M1 | Docker 환경 + FastAPI 기본 구조 + SQLite 스키마 |
| M2 | 인풋 관리 (등록/삭제/리스트) + Claude 판단 연동 |
| M3 | Playwright 크롤링 + APScheduler |
| M4 | Claude 정제 + DB 저장 |
| M5 | Next.js 블로그 UI + 애니메이션 |
| M6 | CI/CD + 배포 |

---

## PROGRESS.md 작업 규칙

- 작업 시작 전 전체 STEP 항목 먼저 기록
- 각 STEP 완료 직후 즉시 [x] 업데이트 (일괄 금지)
- 에러 시 `❌ 에러: <내용>` 기록 후 중단·보고

```
## STEP N: 작업명 (날짜)
- [ ] STEP N-1: 세부 작업
- [ ] STEP N-2: 세부 작업
- [x] STEP N-3: 완료된 작업
```

파일 위치: `~/PROGRESS.md`
