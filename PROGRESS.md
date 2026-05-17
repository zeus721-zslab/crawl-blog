# crawl-blog — 작업 진행 현황

## STEP 39: judge_input URL 실존 검증 추가 (2026-05-17)
- [x] STEP 39-1: PROGRESS.md 기록
- [x] STEP 39-2: main.py — check_url_reachable() 함수 추가
- [x] STEP 39-3: main.py — URL 직접 입력 시 LLM 호출 전 URL 검증
- [x] STEP 39-4: main.py — 키워드 입력 시 target_sites 각 URL 검증 후 skip

## STEP 38: UI 버그 수정 + 피드 관리 개선 (2026-05-17)
- [x] STEP 38-1: PROGRESS.md 기록
- [x] STEP 38-2: backend — judge_input name 저장 확인 (변경 불필요 확인)
- [x] STEP 38-3: manage/page.tsx — error_message 표시 조건 수정 (status=failed || error_message)
- [x] STEP 38-4: page.tsx — ⚠ 아이콘 및 관련 로직 완전 제거
- [x] STEP 38-5: page.tsx — 탭 overflow 드롭다운 구현 (5개 초과 시 PC 드롭다운, 모바일 스크롤 유지)

## STEP 37: MD 파일 업데이트 (2026-05-17)
- [x] STEP 37-1: PROGRESS.md 기록
- [x] STEP 37-2: README.md — 기술 스택/기능/API/구조 최신화
- [x] STEP 37-3: CRAWL-BLOG.md — 아키텍처/상태/provider 최신화

## STEP 36: 탭 UI + 애니메이션 전면 개선 (2026-05-17)
- [x] STEP 36-1: PROGRESS.md 기록
- [x] STEP 36-2: scheduler.py — 0건 시 error_message, 성공 시 None
- [x] STEP 36-3: page.tsx — STATUS paused 추가, TabBtn layoutId 슬라이딩 인디케이터
- [x] STEP 36-4: page.tsx — 탭 ⚠ 조건 (active+0건, failed+tooltip)
- [x] STEP 36-5: page.tsx — PostCard variants + hover shadow, stagger 수정
- [x] STEP 36-6: page.tsx — FeedInfoCard error_message 조건 확장 + 애니메이션
- [x] STEP 36-7: page.tsx — 콘텐츠 영역 tab 전환 시 fade 전환

## STEP 35: 피드 에러 표시 + 중단/재개 기능 (2026-05-17)
- [x] STEP 35-1: PROGRESS.md 기록
- [x] STEP 35-2: database.py — error_message 컬럼 추가 (DDL + ALTER TABLE)
- [x] STEP 35-3: scheduler.py — force 파라미터 + paused/failed skip + error_message 저장
- [x] STEP 35-4: main.py — InputUpdate status 필드 + PATCH 핸들러 + trigger_crawl paused 차단
- [x] STEP 35-5: frontend/page.tsx — error_message 타입 + 탭 에러 아이콘 + FeedInfoCard 에러 표시
- [x] STEP 35-6: frontend/manage/page.tsx — error_message + paused 상태 + 중단/재개 버튼 + 에러 표시

## STEP 34: RSS source_url 버그 수정 — 피드 URL 자동 감지 (2026-05-17)
- [x] STEP 34-1: PROGRESS.md 기록
- [x] STEP 34-2: scheduler.py — 피드 URL 자동 감지 후 method="rss" 전환

## STEP 33: fetch_links Playwright fallback 조건 완화 (2026-05-17)
- [x] STEP 33-1: PROGRESS.md 기록
- [x] STEP 33-2: crawler.py — fallback 조건 < 3 → <= 5

## STEP 32: LLM mock provider 추가 (2026-05-17)
- [x] STEP 32-1: PROGRESS.md 기록
- [x] STEP 32-2: backend/llm/mock.py 생성
- [x] STEP 32-3: backend/llm/factory.py — mock 분기 추가
- [x] STEP 32-4: .env.example — LLM_PROVIDER=mock 주석 추가

## STEP 31: fetch_links 디버깅 + Playwright fallback (2026-05-17)
- [x] STEP 31-1: PROGRESS.md 기록
- [x] STEP 31-2: crawler.py — fetch_links 추출 수 INFO 로그 + 3개 미만 시 Playwright fallback

## STEP 30: _is_likely_article 오탐 수정 (2026-05-17)
- [x] STEP 30-1: PROGRESS.md 기록
- [x] STEP 30-2: crawler.py — _NAV_SEGMENTS에서 "page"/"video"/"videos" 제거, 단일 세그먼트 기준 > 25 → > 15

## STEP 29: 링크 추출 로직 개선 — 기사 URL 필터링 (2026-05-17)
- [x] STEP 29-1: PROGRESS.md 기록
- [x] STEP 29-2: crawler.py — _NAV_SEGMENTS / _DATE_RE 상수 추가, _is_likely_article 헬퍼 추가, _extract_article_links 필터 적용

## STEP 28: 백그라운드 태스크 로그 미출력 수정 (2026-05-17)
- [x] STEP 28-1: PROGRESS.md 기록
- [x] STEP 28-2: main.py — module-level basicConfig(INFO) 추가
- [x] STEP 28-3: scheduler.py, crawler.py 로거 설정 확인 (변경 불필요 — propagate 정상)

## STEP 27: 백그라운드 태스크 로깅 전면 개선 (2026-05-17)
- [x] STEP 27-1: PROGRESS.md 기록
- [x] STEP 27-2: scheduler.py — crawl_input 전체 try/except 감싸기 + start/abort 로그
- [x] STEP 27-3: main.py — logging 추가, _bg_task_done 콜백 추가

## STEP 26: scheduler.py 로깅 개선 (2026-05-17)
- [x] STEP 26-1: PROGRESS.md 기록
- [x] STEP 26-2: scheduler.py 로그 레벨 및 메시지 수정
- [x] STEP 26-3: git push

## STEP 25: 퀄리티 개선 4가지 (2026-05-17)
- [x] STEP 25-1: PROGRESS.md 기록
- [x] STEP 25-2: database.py — keyword 컬럼 추가, create_input keyword 파라미터
- [x] STEP 25-3: main.py — keyword/topic 입력 시 keyword 저장
- [x] STEP 25-4: llm/base.py — REFINE_SYSTEM 업데이트, ABC 시그니처 변경
- [x] STEP 25-5: llm/claude.py — refine_content 시그니처 + user 메시지 변경
- [x] STEP 25-6: llm/gemini.py, groq.py, ollama.py — refine_content 시그니처 변경
- [x] STEP 25-7: crawler.py — _extract_article_links + fetch_links 추가
- [x] STEP 25-8: scheduler.py — name/keyword 전달, RSS 본문 fetch, HTML dedup 개선, skip 처리

## STEP 24: 피드 name 컬럼 + 탭 UI 개선 (2026-05-17)
- [x] STEP 24-1: PROGRESS.md 기록
- [x] STEP 24-2: database.py — inputs.name 컬럼 추가, create_input name 파라미터
- [x] STEP 24-3: llm/base.py — JUDGE_SYSTEM name 필드 추가
- [x] STEP 24-4: main.py — name 추출·저장, PATCH name 지원
- [x] STEP 24-5: page.tsx — 탭 name 표시, 피드 정보 카드, 피드 목록 탭
- [x] STEP 24-6: manage/page.tsx — name 표시 + 인라인 편집

## STEP 23: scheduler async generator / task destroyed 에러 수정 (2026-05-17)
- [x] STEP 23-1: PROGRESS.md 기록
- [x] STEP 23-2: crawler.py — async_playwright() async with → start()/stop() 패턴 전환
- [x] STEP 23-3: main.py — create_task 참조 유지 (_bg_tasks set)

## STEP 22: refine_content max_tokens 및 REFINE_SYSTEM 프롬프트 강화 (2026-05-17)
- [x] STEP 22-1: PROGRESS.md 기록
- [x] STEP 22-2: claude.py refine_content max_tokens 2048 → 4096
- [x] STEP 22-3: base.py REFINE_SYSTEM content 길이 제한 추가

## STEP 21: docker-compose backend networks zslab_zslab_net 추가 (2026-05-17)
- [x] STEP 21-1: PROGRESS.md 기록
- [x] STEP 21-2: docker-compose backend networks에 zslab_zslab_net 추가
- [x] STEP 21-3: git push

## STEP 20: SQLite → MariaDB 전환 (2026-05-17)
- [x] STEP 20-1: PROGRESS.md 기록
- [x] STEP 20-2: requirements.txt — aiosqlite → aiomysql + cryptography
- [x] STEP 20-3: settings.py — DB 접속 필드 추가
- [x] STEP 20-4: database.py — aiomysql 전환 전면 수정
- [x] STEP 20-5: .env.example — DB 환경변수 추가
- [x] STEP 20-6: docker-compose — backend DB 환경변수 추가
- [x] STEP 20-7: scheduler.py — jobstore URL sqlite → mysql+pymysql
- [x] STEP 20-8: requirements.txt — pymysql 추가 (SQLAlchemy jobstore용)

## STEP 19: SQLite → MariaDB 전환 준비 파일 확인 (2026-05-17)
- [x] STEP 19-1: PROGRESS.md 기록
- [x] STEP 19-2: database.py 확인
- [x] STEP 19-3: requirements.txt 확인
- [x] STEP 19-4: .env.example 확인

## STEP 18: DB CHECK constraint 'pending' 추가 (2026-05-17)
- [x] STEP 18-1: PROGRESS.md 기록
- [x] STEP 18-2: database.py CHECK constraint 수정

## STEP 17: deploy.yml ssh-action 버전 고정 (2026-05-16)
- [x] STEP 17-1: PROGRESS.md 기록
- [x] STEP 17-2: appleboy/ssh-action@v1 → @v1.0.3 변경 + push

## STEP 16: database.py get_db() Thread 재시작 오류 수정 (2026-05-16)
- [x] STEP 16-1: PROGRESS.md 기록
- [x] STEP 16-2: get_db() → asynccontextmanager 전환, 호출부 전체 수정
- [x] STEP 16-3: git push

## STEP 15: deploy.yml + Dockerfile 빌드 환경변수 수정 (2026-05-16)
- [x] STEP 15-1: PROGRESS.md 기록
- [x] STEP 15-2: frontend/Dockerfile — builder 스테이지에 ARG/ENV 추가
- [x] STEP 15-3: deploy.yml — build-args 주입, repo 소문자 정규화
- [x] STEP 15-4: git push

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
