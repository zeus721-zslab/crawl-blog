# crawl-blog — 아키텍처 문서

## 서비스 개요

URL 또는 키워드를 입력받아 LLM이 크롤링 가능 여부를 판단하고,
APScheduler가 주기적으로 수집 → LLM이 정제 → 블로그 형태로 누적 제공하는 개인용 서비스.

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| 프론트 | Next.js 15 (App Router) + TypeScript + Tailwind CSS + Framer Motion |
| 백엔드 | FastAPI (Python 3.12) |
| AI | claude / gemini / groq / ollama / mock (환경변수로 선택) |
| 크롤링 | feedparser (RSS) → BeautifulSoup (HTML) → Playwright (JS fallback) |
| 스케줄링 | APScheduler (persistent MySQL jobstore, max_instances=1, coalesce=True) |
| DB | MariaDB (aiomysql) |
| 배포 | Docker + gateway_nginx + GitHub Actions |

---

## 핵심 흐름

```
사용자 입력 (URL 또는 키워드 + 비밀번호)
→ FastAPI 비밀번호 검증
→ LLM 판단 (judge_input)
  → URL: crawl_method 결정 (rss | html | playwright) + 피드 등록
  → 키워드: 추천 target_sites 최대 3개 자동 등록
  → 불가: 이유 저장, 상태 = rejected
→ APScheduler 주기적 실행 (1h / 6h / 24h)
  → 피드 URL 패턴 자동 감지 (/feed, /rss, /atom 등) → rss 방식 강제
  → RSS: feedparser → 개별 기사 URL 추출 → 본문 fetch → LLM 정제
  → HTML/Playwright: 목록 페이지 링크 추출 (≤5개면 Playwright 재시도) → 기사 fetch → LLM 정제
  → 신규 source_url만 처리 (DB 중복 체크)
  → 회차당 최대 3건 정제 (MAX_REFINE_PER_RUN)
  → 일일 전체 호출 캡 초과 시 중단 (CLAUDE_DAILY_LIMIT)
  → 완료 후 error_message 초기화 (성공) 또는 "수집 가능한 콘텐츠를 찾지 못했습니다" (0건)
→ MariaDB 저장
→ Next.js 블로그 렌더링
```

---

## LLM Provider

`LLM_PROVIDER` 환경변수로 선택. 모두 동일한 `LLMProvider` ABC 구현.

| Provider | 용도 | 비고 |
|----------|------|------|
| `claude` | 기본값. Haiku(판단) + Sonnet(정제) | ANTHROPIC_API_KEY 필요 |
| `gemini` | Google Gemini | GEMINI_API_KEY 필요 |
| `groq` | Groq (Llama 계열) | GROQ_API_KEY 필요 |
| `ollama` | 로컬 Ollama | OLLAMA_BASE_URL 설정 |
| `mock` | API 호출 없음, 흐름 테스트용 | 키 불필요 |

LLMProvider ABC 메서드:
- `judge_input(value)` → `{approved, reason, crawl_method, name, target_sites}`
- `refine_content(raw, source_url, feed_name, keyword)` → `{title, content, summary, tags, skip?}`

---

## 피드 상태 (inputs.status)

| 상태 | 설명 |
|------|------|
| `active` | 정상 활성, 스케줄 크롤링 대상 |
| `crawling` | 크롤링 진행 중 |
| `paused` | 사용자가 수동 중단, 스케줄 크롤링 skip |
| `failed` | 크롤링 오류 발생, 스케줄 크롤링 skip, error_message 저장 |
| `rejected` | LLM 판단 불가 |
| `deleted` | 삭제됨 (소프트 삭제) |

- `paused` / `failed` 상태에서 수동 크롤링 트리거 가능 (`force=True`)
- `paused` 상태에서 수동 크롤링 트리거는 API에서 409 차단 (재개 후 가능)
- 재개(`status → active`) 시 `error_message` 자동 초기화

---

## 크롤링 방식

### RSS

```
fetch_rss(url)
→ feedparser 파싱 → 최대 10개 entry
→ 각 entry.url 에 대해:
    fetch_page(url, method="html")  # 본문 전체 fetch 시도
    실패 시 entry.summary 폴백
→ refine_content
```

### HTML / Playwright

```
fetch_links(url)
→ httpx GET → _extract_article_links (BeautifulSoup)
→ 추출 수 ≤ 5 → Playwright로 재시도
→ 링크 없으면 페이지 자체를 단일 기사로 처리
→ 각 article_url:
    fetch_page(url, method)
    실패 시 Playwright fallback
→ refine_content
```

### 피드 URL 자동 감지

`crawl_method` 가 `null`/`html` 이더라도, URL 경로에 `/feed`, `/rss`, `/atom`, `.rss`, `.atom`, `feed.xml` 포함 시 자동으로 `rss` 방식 전환.

### 기사 URL 필터링 (`_is_likely_article`)

- `_NAV_SEGMENTS` 에 속하는 첫 세그먼트 제외 (category, tag, author, archive 등)
- 미디어 확장자 제외 (jpg, pdf, mp3 등)
- 날짜 패턴(`/20\d{2}/`) 포함 → 기사로 인정
- 2개 이상 세그먼트 → 기사로 인정
- 단일 세그먼트: 슬러그 길이 > 15 시만 인정

---

## inputs 테이블 주요 컬럼

| 컬럼 | 설명 |
|------|------|
| `value` | URL |
| `type` | `url` |
| `name` | LLM이 추출한 피드 표시명 |
| `keyword` | 키워드 등록 시 원본 검색어 |
| `status` | active / crawling / paused / failed / rejected / deleted |
| `error_message` | 크롤링 실패 사유 또는 0건 메시지 |
| `crawl_method` | rss / html / playwright |
| `crawl_interval` | 1h / 6h / 24h |
| `last_crawl_at` | 마지막 크롤링 시각 |
| `next_crawl_at` | 다음 예정 시각 |
| `post_count` | 수집된 글 수 |
| `has_new` | 신규 글 존재 여부 |
| `claude_approved` | LLM 승인 여부 |
| `claude_reason` | LLM 판단 이유 |

---

## 비용 제어

| 장치 | 설명 |
|------|------|
| `MAX_REFINE_PER_RUN = 3` | 스케줄 1회당 최대 정제 건수 |
| `CLAUDE_DAILY_LIMIT` | 일일 전체 정제 호출 캡 (기본 100) |
| `rate.check_and_increment()` | 캡 초과 시 크롤링 중단 |
| `mock` provider | API 크레딧 소모 없이 흐름 테스트 |

---

## APScheduler 설정

```python
jobstores = {
    'default': SQLAlchemyJobStore(url='mysql+pymysql://...')
}
job_defaults = {
    'coalesce': True,          # 밀린 실행은 1회로 합산
    'max_instances': 1,        # 동시 실행 방지
    'misfire_grace_time': 600, # 10분 내 지연 허용
}
scheduler = AsyncIOScheduler(jobstores=jobstores, job_defaults=job_defaults)
```

---

## 디렉토리 구조

```
crawl-blog/
├── frontend/                  # Next.js 15
│   └── src/
│       ├── app/
│       │   ├── page.tsx           # 블로그 메인 (탭·글 목록·검색)
│       │   ├── manage/page.tsx    # 피드 관리
│       │   └── posts/[id]/        # 글 상세
│       └── lib/
│           └── api.ts             # apiFetch 유틸
├── backend/                   # FastAPI
│   ├── main.py                # API 라우터
│   ├── database.py            # MariaDB CRUD
│   ├── crawler.py             # RSS/HTML/Playwright
│   ├── scheduler.py           # APScheduler + crawl_input
│   ├── rate.py                # 일일 LLM 호출 카운터
│   ├── settings.py            # 환경변수 (pydantic-settings)
│   └── llm/
│       ├── base.py            # LLMProvider ABC
│       ├── claude.py
│       ├── gemini.py
│       ├── groq.py
│       ├── ollama.py
│       ├── mock.py            # API 없이 테스트용
│       └── factory.py
├── docker-compose.crawl-blog.yml
├── .github/workflows/deploy.yml
└── .env.example
```

---

## API 엔드포인트

```
POST   /api/inputs              피드 등록 (비밀번호 + LLM 판단)
GET    /api/inputs              피드 목록
DELETE /api/inputs/{id}         피드 삭제 (body: {password})
PATCH  /api/inputs/{id}         interval / name / status 변경
                                status: "paused" (중단) | "active" (재개)

GET    /api/posts               글 목록 (input_id / search / page)
GET    /api/posts/{id}          글 상세
PATCH  /api/posts/{id}/read     읽음 처리

GET    /api/status              시스템 상태 (overall / active_count / llm_remaining)
POST   /api/crawl/{id}          수동 크롤링 트리거 (body: {password})
```

---

## 프론트엔드 주요 UI

- **탭 바** — 전체 / 피드별 / 피드 목록, layoutId 슬라이딩 인디케이터
- **탭 경고 아이콘** — `status=failed` → 빨간 ⚠ (error_message 툴팁), `active+0건` → 앰버 ⚠
- **FeedInfoCard** — 피드 탭 선택 시 상단에 slide-down 등장 (상태·에러·통계)
- **PostCard** — stagger fade-in, hover lift + shadow
- **FeedListTab** — 전체 피드 목록, 클릭 시 해당 피드 탭으로 이동
- **manage/page** — 중단/재개 버튼, 에러 메시지 인라인 표시, 시스템 상태 바

---

## 보안

- bcrypt 비밀번호 검증 (PASSWORD_HASH 환경변수)
- IP rate limiting — 5회 실패 시 15분 잠금
- 도메인 블랙리스트 (DOMAIN_BLACKLIST)
- 인풋 등록·삭제·수동 크롤링 → 비밀번호 필요
- 블로그 조회 → 공개
