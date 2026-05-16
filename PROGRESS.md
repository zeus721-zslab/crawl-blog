# crawl-blog — 작업 진행 현황

## STEP 6: backend Dockerfile Playwright 설치 오류 수정 (2026-05-16)
- [x] STEP 6-1: Dockerfile 수정 (--with-deps 제거, Debian 패키지 직접 설치)
- [ ] STEP 6-2: 커밋 + push

## STEP 5: frontend package-lock.json 재생성 (2026-05-16)
- [x] STEP 5-1: Docker로 npm install 실행 (framer-motion 반영)
- [x] STEP 5-2: 변경된 package-lock.json 커밋 + push

## STEP 4: .gitignore 점검 + GitHub push (2026-05-16)
- [x] STEP 4-1: .gitignore 수정 확정
- [x] STEP 4-2: .gitattributes 생성 (LF 통일)
- [x] STEP 4-3: git init + add + commit
- [x] STEP 4-4: git remote + push

## STEP 3: LLM Provider 추상화 (2026-05-16)
- [x] STEP 3-1: llm/base.py — 추상 클래스 + 공통 프롬프트
- [x] STEP 3-2: llm/claude.py — Anthropic Claude 구현
- [x] STEP 3-3: llm/gemini.py — Google Gemini 구현
- [x] STEP 3-4: llm/groq.py — Groq 구현
- [x] STEP 3-5: llm/ollama.py — Ollama (로컬) 구현
- [x] STEP 3-6: llm/factory.py — LLM_PROVIDER env 기반 팩토리
- [x] STEP 3-7: settings.py 업데이트 (LLM_PROVIDER, API 키들)
- [x] STEP 3-8: main.py — factory 통해 호출로 교체
- [x] STEP 3-9: scheduler.py — factory 통해 호출로 교체
- [x] STEP 3-10: claude.py 호환 shim으로 교체
- [x] STEP 3-11: requirements.txt 선택 패키지 주석 추가
- [x] STEP 3-12: .env.example 업데이트

## STEP 2: 전체 파일 검토 및 수정/보완 (2026-05-16)
- [x] STEP 2-1: docker-compose 네트워크 수정 + image 태그 추가
- [x] STEP 2-2: requirements.txt feedparser 추가
- [x] STEP 2-3: main.py import 정리 (Depends 제거, asyncio 상단 이동)
- [x] STEP 2-4: settings.py + crawler.py 도메인 블랙리스트 구현
- [x] STEP 2-5: deploy.yml 서버 경로 /home/crawl-blog/ 고정
- [x] STEP 2-6: .env.example 생성
- [x] STEP 2-7: frontend 스켈레톤 페이지 생성 (manage/, posts/[id]/)

## STEP 1: 프로젝트 초기 세팅 (2026-05-16)
- [x] STEP 1-1: PROGRESS.md 작성
- [x] STEP 1-2: frontend/ — Next.js 15 초기화 (Docker)
- [x] STEP 1-3: backend/ — FastAPI 기본 구조 생성
- [x] STEP 1-4: docker-compose.crawl-blog.yml 작성
- [x] STEP 1-5: .gitignore 생성
- [x] STEP 1-6: GitHub Actions deploy.yml 작성
- [x] STEP 1-7: README.md 작성
