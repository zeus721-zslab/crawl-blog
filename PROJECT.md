# crawl-blog — 프로젝트 규칙

## 참조 파일
CRAWL-BLOG.md 를 반드시 먼저 읽고 작업할 것.

## 기술 스택
- Frontend: Next.js 15 (App Router) + TypeScript + Tailwind CSS + Framer Motion
- Backend: FastAPI (Python)
- AI: Claude API
- 크롤링: Playwright + BeautifulSoup
- 스케줄링: APScheduler
- DB: SQLite
- 배포: Docker + gateway_nginx + GitHub Actions

## 디렉토리
- C:\Users\pc\projects\crawl-blog\ — 프로젝트 루트
- frontend/ — Next.js
- backend/ — FastAPI

## 환경
- 로컬 개발: Docker 기반 (Node.js/Python 로컬 설치 없음)
- 배포: 서버 Docker + gateway_nginx
CLAUDE.md 는 zslab.dev 것 그대로 복사하면 돼.

3. VS Code로 폴더 열기
powershellcode C:\Users\pc\projects\crawl-blog

4. Claude Code 시작 프롬프트
CRAWL-BLOG.md, PROJECT.md 읽고 프로젝트 초기 세팅 시작.

작업 순서:
1. frontend/ — Next.js 15 초기화 (Docker로)
2. backend/ — FastAPI 기본 구조 생성
3. docker-compose.crawl-blog.yml 작성
4. .gitignore 생성
5. GitHub Actions deploy.yml 작성
6. README.md 작성

로컬 개발 환경: Docker 기반, Node.js/Python 로컬 설치 없음.