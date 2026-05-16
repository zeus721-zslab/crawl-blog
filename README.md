# crawl-blog

키워드/URL을 입력받아 Claude API가 자동 크롤링 여부를 판단하고, 수집된 정보를 블로그 형태로 누적 제공하는 개인용 서비스.

## 기술 스택

| 영역 | 기술 |
|------|------|
| 프론트 | Next.js 15 · TypeScript · Tailwind CSS · Framer Motion |
| 백엔드 | FastAPI (Python 3.12) |
| AI | Claude API (claude-opus-4-7) |
| 크롤링 | Playwright · BeautifulSoup |
| 스케줄링 | APScheduler |
| DB | SQLite |
| 배포 | Docker · gateway_nginx · GitHub Actions |

## 로컬 개발 (Docker 필수)

### 1. 환경 변수

```bash
cp .env.example .env
# .env 편집: ANTHROPIC_API_KEY, PASSWORD_HASH 입력
```

PASSWORD_HASH 생성 (Python):

```python
import bcrypt
print(bcrypt.hashpw(b"your-password", bcrypt.gensalt()).decode())
```

### 2. 실행

```bash
docker compose -f docker-compose.crawl-blog.yml up --build
```

- 프론트엔드: http://localhost:3000
- 백엔드 API: http://localhost:8000
- API 문서: http://localhost:8000/docs

## 배포

`main` 브랜치에 push하면 GitHub Actions가 자동으로:
1. frontend/backend Docker 이미지 빌드 → ghcr.io 푸시
2. 서버 SSH 접속 → `docker compose pull && up`

### GitHub Secrets 설정

| Key | 설명 |
|-----|------|
| `SERVER_HOST` | 서버 IP/도메인 |
| `SERVER_USER` | SSH 사용자명 |
| `SERVER_SSH_KEY` | SSH 개인키 |
| `PROJECT_PATH` | 서버 내 프로젝트 경로 |

## 프로젝트 구조

```
crawl-blog/
├── frontend/               # Next.js 15
│   ├── src/app/
│   │   ├── page.tsx        # 블로그 메인
│   │   ├── manage/         # 인풋 관리
│   │   └── posts/[id]/     # 글 상세
│   └── Dockerfile
├── backend/                # FastAPI
│   ├── main.py             # 라우터
│   ├── database.py         # SQLite
│   ├── claude.py           # Claude API
│   ├── crawler.py          # Playwright
│   ├── scheduler.py        # APScheduler
│   ├── settings.py         # 환경변수
│   └── Dockerfile
├── docker-compose.crawl-blog.yml
├── .github/workflows/deploy.yml
└── CRAWL-BLOG.md           # 기획서
```

## API 엔드포인트

```
POST   /api/inputs              인풋 등록 (비밀번호 + Claude 판단)
GET    /api/inputs              인풋 목록
DELETE /api/inputs/{id}        인풋 삭제
PATCH  /api/inputs/{id}        크롤링 주기 변경

GET    /api/posts               글 목록 (검색/필터/페이지)
GET    /api/posts/{id}          글 상세
PATCH  /api/posts/{id}/read     읽음 처리

GET    /api/status              시스템 상태
POST   /api/crawl/{id}         수동 크롤링 트리거
GET    /api/claude/stream       Claude 판단 SSE 스트리밍
```

## 개발 마일스톤

| 단계 | 내용 | 상태 |
|------|------|------|
| M1 | Docker 환경 + FastAPI 기본 구조 + SQLite 스키마 | ✅ |
| M2 | 인풋 관리 UI + Claude 판단 연동 | - |
| M3 | Playwright 크롤링 + APScheduler | - |
| M4 | Claude 정제 + DB 저장 | - |
| M5 | Next.js 블로그 UI + 애니메이션 | - |
| M6 | CI/CD + 배포 | - |
