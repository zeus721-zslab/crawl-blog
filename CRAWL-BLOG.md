# crawl-blog — 프로젝트 기획서 (MVP)

## 서비스 개요

URL을 입력받아 Claude API가 크롤링 가능 여부를 판단하고,
APScheduler가 주기적으로 수집 → Claude가 정제 → 블로그 형태로 누적 제공하는
개인용 + 포폴용 사이트.

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| 프론트 | Next.js 15 (App Router) + TypeScript + Tailwind CSS + Framer Motion |
| 백엔드 | FastAPI (Python) |
| AI | Claude Haiku (판단) + Claude Sonnet (정제) |
| 크롤링 | feedparser (RSS) → BeautifulSoup (HTML) → Playwright (JS fallback) |
| 스케줄링 | APScheduler (persistent SQLite jobstore, max_instances=1, coalesce=True) |
| DB | SQLite |
| 배포 | Docker + gateway_nginx + GitHub Actions |

---

## 핵심 흐름

```
사용자 입력 (URL + 비밀번호)
→ FastAPI 비밀번호 검증
→ Claude Haiku 판단 (1회)
  → 가능: crawl_method 결정 (rss | html | playwright) + 등록
  → 불가능: 이유 저장 → 리스트에 표기
→ 등록 즉시 결과 카드 표시 (판단 결과 + crawl_method)
→ APScheduler 주기적 실행 (persistent, coalesce, max_instances=1)
  → RSS 우선 → HTML → Playwright fallback
  → 신규 항목만 Claude Sonnet 정제 (1건당 1회, 최대 N건/회차)
  → 중복 URL 스킵
→ SQLite 저장
→ Next.js 블로그 렌더링
```

---

## 비용 설계

**목표: $15 크레딧으로 5개월 유지 ($3/월)**

### 모델별 역할

| 용도 | 모델 | 단가 (input/output) | 이유 |
|------|------|---------------------|------|
| 판단 | claude-haiku-4-5 | $0.80 / $4.00 per M tok | 최저비용, 판단은 간단 |
| 정제 | claude-sonnet-4-5 | $3.00 / $15.00 per M tok | 블로그 품질 유지 |

### 호출 횟수 설계

| 단계 | 호출 조건 | 제한 |
|------|-----------|------|
| 판단 | URL 등록 시 1회 | 무제한 (Haiku, 비용 미미) |
| 정제 | 신규 아티클 발견 시 1건당 1회 | 회차당 최대 3건 처리 |

### 월간 비용 추정 (안정 운영 기준: URL 5개)

```
판단: 월 등록 ~5건 × 1회 × ~0.001$ ≈ $0.005 (무시)

정제 (Sonnet):
  - 5 URLs × 24회/월 (매일) × 평균 1건/회차 = 120건/월
  - 건당: input ~1,500 tok + output ~800 tok
  - 120 × ($0.0045 + $0.012) = 약 $1.98/월

합계: 약 $2.0/월 ← $3 이하 유지 ✓
```

### 초기 데이터 축적 (오늘~내일)

- URL 최대 20개 등록 허용
- 6시간 주기로 1회씩만 실행
- 20 URLs × 2회 × 2일 × 평균 1건 = 80건 정제
- 80 × $0.0165 ≈ $1.32 (1회성)

### 안전장치

- `CLAUDE_DAILY_LIMIT`: 환경변수로 일일 Sonnet 호출 캡 설정 (기본 30)
- 연속 실패 3회 시 해당 URL 상태 → `failed`, 스케줄링 중단

---

## 기능 상세

### 1. 인풋 관리 (URL 전용)

- **입력**: URL + 비밀번호 (키워드 입력 제거)
- **등록 흐름**: 제출 → 로딩 → 완료 후 판단 결과 카드 표시
- 리스트 표시 항목:
  - URL
  - 상태: `활성` / `크롤링 중` / `실패` / `불가` / `삭제됨`
  - Claude 판단 결과 (가/부 + 이유 + crawl_method)
  - 마지막 크롤링 시간 / 다음 예정 시간
  - 수집된 글 수 / NEW 뱃지
  - 크롤링 주기 설정 (6시간 / 매일 / 수동만)
  - 삭제 버튼
- 삭제 시 스케줄링에서 즉시 제외

### 2. Claude 판단 (Haiku, 등록 시 1회)

- URL의 크롤링 가능 여부 분석
- 수집 방식 결정: `rss` / `html` / `playwright`
- 불가 시 이유 명확히 저장, 리스트에 표기
- **Streaming 없음**: 등록 완료 후 결과 카드로 표시

### 3. 크롤링 (우선순위 적용)

크롤러 선택 순서:
```
1. RSS: feedparser로 피드 확인 → 있으면 사용 (Playwright 불필요)
2. HTML: requests + BeautifulSoup (JS 불필요한 정적 사이트)
3. Playwright: JS 렌더링 필요한 경우만 fallback
```

제한:
- 회차당 신규 아티클 최대 **3건**만 정제 (비용 제어)
- 이미 수집된 source_url은 스킵 (DB 중복 체크)
- 정제 실패 시 해당 아티클 스킵, 로그 기록

### 4. Claude 정제 (Sonnet, 아티클당 1회)

- 핵심 내용 요약
- 마크다운 블로그 형태로 재구성
- 태그 자동 추출 (3~5개)
- 실패 시 raw text를 title + content에 그대로 저장 (정제 실패 표기)

### 5. 결과물 (블로그)

- 수집된 글 누적 표시
- 최신순 / URL별 탭 분리
- 읽음 / 안읽음 처리
- NEW 뱃지
- 글 내용 검색
- URL별 필터링

### 6. 보안

- bcrypt 해싱된 비밀번호 검증
- 5회 실패 시 IP 잠금 15분 (rate limiting)
- `CLAUDE_DAILY_LIMIT` 환경변수로 일일 Sonnet 호출 캡
- 인풋 등록/삭제/수동 크롤링 → 비밀번호 필요
- 블로그 결과물 조회 → 공개
- 크롤링 대상 도메인 블랙리스트 적용
- HTTPS 필수 (gateway_nginx SSL)

---

### 7. 시스템 상태 패널

항상 노출되는 상태 패널:

- 전체 시스템 상태: `정상` / `경고` / `중단`
- 항목별 상태:
  - 활성 URL 수
  - Claude Sonnet 일일 잔여 호출 수
  - 스케줄러 실행 상태 (동작 중 / 중단)
  - 마지막 크롤링 성공 시간
- 중단 원인:
  - 활성 URL 없음
  - 일일 Sonnet 한도 초과
  - 크롤링 연속 실패

---

## APScheduler 설정

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:////app/data/jobs.db')
}
job_defaults = {
    'coalesce': True,       # 밀린 실행은 1회로 합산
    'max_instances': 1,     # 동시 실행 방지
    'misfire_grace_time': 60 * 10,  # 10분 내 지연 허용
}
scheduler = AsyncIOScheduler(jobstores=jobstores, job_defaults=job_defaults)
```

---

## 디렉토리 구조

```
crawl-blog/
├── frontend/          # Next.js 15
│   └── src/
│       ├── app/
│       │   ├── page.tsx          # 블로그 메인 (글 목록)
│       │   ├── manage/page.tsx   # URL 관리
│       │   └── posts/[id]/       # 글 상세
│       └── lib/
│           └── api.ts            # fetch 유틸
├── backend/           # FastAPI
│   ├── main.py        # API 라우터
│   ├── crawler.py     # RSS → HTML → Playwright
│   ├── scheduler.py   # APScheduler (persistent)
│   ├── llm/           # LLM provider 추상화
│   │   ├── base.py
│   │   ├── claude.py  # Haiku(판단) + Sonnet(정제) 분리
│   │   └── factory.py
│   ├── database.py    # SQLite
│   └── settings.py
├── docker-compose.crawl-blog.yml
├── .github/workflows/deploy.yml
└── PROJECT.md
```

---

## API 엔드포인트 (FastAPI)

```
POST /api/inputs          — URL 등록 (비밀번호 검증 + Claude Haiku 판단)
GET  /api/inputs          — URL 목록 조회
DELETE /api/inputs/{id}   — URL 삭제 (body: {password})
PATCH /api/inputs/{id}    — 주기 변경 (body: {interval, password})

GET  /api/posts           — 글 목록 (필터/검색/페이지네이션)
GET  /api/posts/{id}      — 글 상세
PATCH /api/posts/{id}/read — 읽음 처리

GET  /api/status          — 시스템 상태 조회
POST /api/crawl/{id}      — 수동 크롤링 트리거 (body: {password})
```

삭제된 엔드포인트:
- ~~GET /api/claude/stream~~ (Streaming 제거)

---

## 디자인 원칙

- 테이블 형태 금지 → 카드/리스트
- Framer Motion 애니메이션 (60fps, transform/opacity만)
  - 페이지 진입 stagger fade-in
  - 리스트 아이템 spring 추가/삭제
  - 상태 변경 시 색상 전환
  - 카드 hover glow + lift
  - **등록 완료 후 판단 결과 카드 slide-in** (streaming 대체)
- 텍스트 명확하게 (높은 contrast)
- 폰트 사이즈 약간 크게
- 모바일 반응형

---

## 개발 마일스톤

| 단계 | 내용 | 상태 |
|------|------|------|
| M1 | Docker 환경 + FastAPI 기본 구조 + SQLite 스키마 | ✅ 완료 |
| M2 | URL 관리 UI + Claude 판단 결과 카드 표시 | ✅ 완료 |
| M3 | RSS→HTML→Playwright 크롤러 + APScheduler (persistent) | 🔲 다음 |
| M4 | Claude Sonnet 정제 + DB 저장 + 중복 스킵 | 🔲 |
| M5 | 블로그 UI 퀄리티 + 비용 모니터링 | 🔲 |
| M6 | CI/CD + 배포 + 운영 설정 | 🔲 |

---

## PROGRESS.md 작업 규칙

- 작업 시작 전 전체 STEP 항목 먼저 기록
- 각 STEP 완료 직후 즉시 [x] 업데이트 (일괄 금지)
- 에러 시 `❌ 에러: <내용>` 기록 후 중단·보고

```
## STEP N: 작업명 (날짜)
- [ ] STEP N-1: 세부 작업
- [x] STEP N-2: 완료된 작업
```

파일 위치: `~/PROGRESS.md`
