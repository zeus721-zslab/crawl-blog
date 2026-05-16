# crawl-blog — 작업 진행 현황

## STEP 15: deploy.yml + Dockerfile 빌드 환경변수 수정 (2026-05-16)
- [x] STEP 15-1: PROGRESS.md 기록
- [x] STEP 15-2: frontend/Dockerfile — builder 스테이지에 ARG/ENV 추가
- [x] STEP 15-3: deploy.yml — build-args 주입, repo 소문자 정규화
- [ ] STEP 15-4: git push

## STEP 14: UI 텍스트/shimmer/SSL 3종 작업 (2026-05-16)
- [x] STEP 14-1: PROGRESS.md 기록
- [x] STEP 14-2: UI 텍스트 인풋→피드 전환 (manage/page.tsx)
- [x] STEP 14-3: SystemStatusBar shimmer 제거
- [x] STEP 14-4: 서버 기존 nginx conf 확인 (명령어 출력, 사용자가 직접 실행)
- [ ] STEP 14-5: certbot SSL 발급 — 서버에서 직접 진행 (제외)
- [ ] STEP 14-6: nginx 443 블록 추가 — 서버에서 직접 진행 (제외)
- [x] STEP 14-7: git push (프론트 변경분)

## STEP 13: 자유 문장 입력 지원 (2026-05-16)
- [x] STEP 13-1: PROGRESS.md 기록
- [x] STEP 13-2: llm/base.py — JUDGE_SYSTEM 프롬프트 URL/키워드 분기
- [x] STEP 13-3: llm/claude.py — judge_input 입력 타입 레이블 전달
- [x] STEP 13-4: main.py — URL 검증 제거, 키워드→URL 등록 흐름
- [x] STEP 13-5: manage/page.tsx — input type/placeholder, JudgmentCard 추천 URL 표시
- [x] STEP 13-6: git push

## STEP 12: ESLint 에러 수정 2 (2026-05-16)
- [x] STEP 12-1: PROGRESS.md 기록
- [x] STEP 12-2: posts/[id]/page.tsx — <a> → <Link /> 교체
- [x] STEP 12-3: page.tsx — " → &quot; 교체
- [x] STEP 12-4: git push

## STEP 11: ESLint 에러 수정 (2026-05-16)
- [x] STEP 11-1: PROGRESS.md 기록
- [x] STEP 11-2: manage/page.tsx — <a> → <Link /> 교체 + push

## STEP 10: MVP 아키텍처 코드 반영 (2026-05-16)
- [x] STEP 10-1: PROGRESS.md 기록
- [x] STEP 10-2: backend/crawler.py — RSS→HTML→Playwright fallback
- [x] STEP 10-3: backend/scheduler.py — persistent jobstore + coalesce + dedup + 3건 캡
- [x] STEP 10-4: backend/llm/ — Haiku(판단) / Sonnet(정제) 분리, stream_judge 제거
- [x] STEP 10-5: backend/rate.py + database.py — refine 카운터 + source_url_exists
- [x] STEP 10-6: backend/main.py — stream 엔드포인트 제거, URL 전용 검증
- [x] STEP 10-7: backend/requirements.txt — sqlalchemy 추가
- [x] STEP 10-8: frontend/manage/page.tsx — SSE 제거, 판단 결과 카드

## STEP 9: CRAWL-BLOG.md MVP 아키텍처 재설계 (2026-05-16)
- [x] STEP 9-1: PROGRESS.md 기록
- [x] STEP 9-2: CRAWL-BLOG.md 전면 재작성 (MVP 반영)

## STEP 8: 디자인 강화 (2026-05-16)
- [x] STEP 8-1: PROGRESS.md 기록
- [x] STEP 8-2: globals.css 디자인 시스템 (shimmer, glow, gradient, pulse 키프레임)
- [x] STEP 8-3: manage/page.tsx 전면 고도화
- [x] STEP 8-4: page.tsx 전면 고도화
- [x] STEP 8-5: posts/[id]/page.tsx 전면 고도화

## STEP 7: M2 Frontend UI 구현 (2026-05-16)
- [x] STEP 7-1: PROGRESS.md STEP 7 항목 기록
- [x] STEP 7-2: globals.css 다크 테마 + layout.tsx 메타데이터 업데이트
- [x] STEP 7-3: frontend/src/lib/api.ts 생성 (API 유틸)
- [x] STEP 7-4: manage/page.tsx 구현 (비밀번호 게이트, 인풋 관리, SSE 스트리밍, 시스템 상태)
- [x] STEP 7-5: page.tsx 구현 (블로그 메인 - 글 목록, 탭, 검색)
- [x] STEP 7-6: posts/[id]/page.tsx 구현 (글 상세)

## STEP 6: backend Dockerfile Playwright 설치 오류 수정 (2026-05-16)
- [x] STEP 6-1: Dockerfile 수정 (--with-deps 제거, Debian 패키지 직접 설치)
- [x] STEP 6-2: 커밋 + push

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
