# crawl-blog

키워드/URL을 입력받아 LLM이 크롤링 여부를 판단하고, 수집된 콘텐츠를 블로그 형태로 누적 제공하는 개인용 서비스.

## 기술 스택

| 영역 | 기술 |
|------|------|
| 프론트 | Next.js 15 · TypeScript · Tailwind CSS · Framer Motion |
| 백엔드 | FastAPI (Python 3.12) |
| AI | Claude · Gemini · Groq · Ollama · Mock (선택) |
| 크롤링 | feedparser (RSS) · BeautifulSoup (HTML) · Playwright (JS fallback) |
| 스케줄링 | APScheduler (persistent MySQL jobstore) |
| DB | MariaDB |
| 배포 | Docker · gateway_nginx · GitHub Actions |

## 주요 기능

- **URL/키워드 등록** — URL 직접 입력 또는 키워드로 추천 사이트 자동 등록
- **LLM 판단** — 크롤링 가능 여부 자동 판단, 수집 방식(rss/html/playwright) 결정
- **자동 크롤링** — RSS 우선 → HTML → Playwright fallback, 주기 설정 (1h/6h/24h)
- **피드 상태 관리** — active / crawling / paused / failed / rejected
- **중단/재개** — 피드별 수동 중단·재개, 실패 시 에러 메시지 표시
- **콘텐츠 정제** — LLM이 요약·태그 추출·마크다운 변환
- **블로그 UI** — 피드 탭 전환, 글 검색, 읽음 처리, NEW 뱃지
- **수동 크롤링** — 즉시 실행 트리거
- **비용 제어** — 일일 LLM 호출 캡 (CLAUDE_DAILY_LIMIT), 도메인 블랙리스트
- **보안** — bcrypt 비밀번호, IP rate limiting (5회 실패 → 15분 잠금)

## 배포 환경 실행

```bash
cp .env.example .env
# .env 편집: ANTHROPIC_API_KEY, PASSWORD_HASH, DB_PASSWORD 입력
docker compose -f docker-compose.crawl-blog.yml up -d
```

`main` 브랜치에 push하면 GitHub Actions가 자동으로 이미지 빌드 → ghcr.io 푸시 → 서버 배포합니다.

### GitHub Secrets

| Key | 설명 |
|-----|------|
| `SERVER_HOST` | 서버 IP/도메인 |
| `SERVER_USER` | SSH 사용자명 |
| `SERVER_SSH_KEY` | SSH 개인키 |
| `PROJECT_PATH` | 서버 내 프로젝트 경로 |

## 환경변수

| 변수 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `PASSWORD_HASH` | ✅ | — | bcrypt 해시 (`python -c "import bcrypt; print(bcrypt.hashpw(b'pw', bcrypt.gensalt()).decode())"`) |
| `LLM_PROVIDER` | | `claude` | `claude` \| `gemini` \| `groq` \| `ollama` \| `mock` |
| `ANTHROPIC_API_KEY` | claude 시 ✅ | — | Claude API 키 |
| `GEMINI_API_KEY` | gemini 시 ✅ | — | Gemini API 키 |
| `GROQ_API_KEY` | groq 시 ✅ | — | Groq API 키 |
| `OLLAMA_BASE_URL` | | `http://localhost:11434` | Ollama 엔드포인트 |
| `CLAUDE_DAILY_LIMIT` | | `100` | 일일 LLM 정제 호출 캡 |
| `NEXT_PUBLIC_API_URL` | | — | 프론트가 호출할 API URL |
| `ALLOWED_ORIGINS` | | `http://localhost:3000` | CORS 허용 도메인 |
| `DOMAIN_BLACKLIST` | | — | 크롤링 금지 도메인 (쉼표 구분) |
| `DB_HOST` | | `zslab_mariadb` | MariaDB 호스트 |
| `DB_PORT` | | `3306` | MariaDB 포트 |
| `DB_USER` | | `crawl_blog` | DB 사용자 |
| `DB_PASSWORD` | ✅ | — | DB 비밀번호 |
| `DB_NAME` | | `crawl_blog` | DB 이름 |

## 프로젝트 구조

```
crawl-blog/
├── frontend/               # Next.js 15
│   ├── src/app/
│   │   ├── page.tsx        # 블로그 메인 (탭·글 목록·검색)
│   │   ├── manage/         # 피드 관리 (등록·삭제·중단·재개)
│   │   └── posts/[id]/     # 글 상세
│   └── Dockerfile
├── backend/                # FastAPI
│   ├── main.py             # API 라우터
│   ├── database.py         # MariaDB (aiomysql)
│   ├── crawler.py          # RSS/HTML/Playwright
│   ├── scheduler.py        # APScheduler
│   ├── rate.py             # 일일 LLM 호출 제한
│   ├── settings.py         # 환경변수
│   ├── llm/
│   │   ├── base.py         # LLMProvider ABC
│   │   ├── claude.py
│   │   ├── gemini.py
│   │   ├── groq.py
│   │   ├── ollama.py
│   │   ├── mock.py         # API 없이 흐름 테스트용
│   │   └── factory.py
│   └── Dockerfile
├── docker-compose.crawl-blog.yml
├── .github/workflows/deploy.yml
└── CRAWL-BLOG.md
```

## API 엔드포인트

```
POST   /api/inputs              피드 등록 (비밀번호 + LLM 판단)
GET    /api/inputs              피드 목록
DELETE /api/inputs/{id}         피드 삭제
PATCH  /api/inputs/{id}         주기·이름·상태(active/paused) 변경

GET    /api/posts               글 목록 (검색/피드 필터/페이지)
GET    /api/posts/{id}          글 상세
PATCH  /api/posts/{id}/read     읽음 처리

GET    /api/status              시스템 상태
POST   /api/crawl/{id}          수동 크롤링 트리거
```
