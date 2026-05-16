'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { apiFetch } from '@/lib/api'

type InputStatus = 'active' | 'crawling' | 'failed' | 'rejected' | 'deleted'
type Period = '1h' | '6h' | '24h'

interface CrawlInput {
  id: number
  value: string
  type: 'keyword' | 'url'
  status: InputStatus
  claude_approved: number | null
  claude_reason: string | null
  crawl_method: string | null
  crawl_interval: Period
  last_crawl_at: string | null
  next_crawl_at: string | null
  post_count: number
  has_new: number
  created_at: string
}

interface SysStatus {
  overall: 'normal' | 'warning' | 'stopped'
  active_count: number
  llm_remaining: number
  scheduler: { running: boolean; job_count: number }
  last_crawl_at: string | null
}

interface JudgmentResult {
  value: string
  approved: boolean
  reason: string
  crawl_method: string | null
  target_sites: string[]
  created_count: number
}

// ── Constants ──────────────────────────────────────────────────────────────

const STATUS_CFG: Record<InputStatus, { label: string; dot: string; chip: string; glow: string }> = {
  active:   { label: '활성',      dot: 'bg-emerald-400 status-glow-active', chip: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/25', glow: 'status-glow-active' },
  crawling: { label: '크롤링 중', dot: 'bg-blue-400 status-glow-crawl',    chip: 'bg-blue-500/10 text-blue-400 border-blue-500/25',         glow: 'status-glow-crawl' },
  failed:   { label: '실패',      dot: 'bg-red-400 status-glow-fail',      chip: 'bg-red-500/10 text-red-400 border-red-500/25',            glow: 'status-glow-fail' },
  rejected: { label: '불가',      dot: 'bg-zinc-500',                      chip: 'bg-zinc-800/60 text-zinc-400 border-zinc-700/50',         glow: '' },
  deleted:  { label: '삭제됨',    dot: 'bg-zinc-700',                      chip: 'bg-zinc-900/60 text-zinc-600 border-zinc-800/50',         glow: '' },
}

const PERIOD_LABELS: Record<Period, string> = { '1h': '1시간', '6h': '6시간', '24h': '매일' }

const SPRING = { type: 'spring', stiffness: 380, damping: 32 } as const

// ── Helpers ────────────────────────────────────────────────────────────────

function isoNorm(iso: string) {
  return iso.includes('Z') || iso.includes('+') ? iso : iso + 'Z'
}
function timeAgo(iso: string | null): string {
  if (!iso) return '없음'
  const min = Math.floor((Date.now() - new Date(isoNorm(iso)).getTime()) / 60000)
  if (min < 1)  return '방금 전'
  if (min < 60) return `${min}분 전`
  const hr = Math.floor(min / 60)
  if (hr < 24)  return `${hr}시간 전`
  return `${Math.floor(hr / 24)}일 전`
}
function fmtTime(iso: string | null): string {
  if (!iso) return '—'
  return new Date(isoNorm(iso)).toLocaleString('ko-KR', {
    month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

// ── SystemStatusBar ────────────────────────────────────────────────────────

const OVERALL_CFG = {
  normal:  { label: '정상', dotCls: 'bg-emerald-400', dotGlow: 'shadow-[0_0_8px_rgba(52,211,153,0.8)]', wrap: 'border-emerald-500/15 bg-emerald-500/5' },
  warning: { label: '경고', dotCls: 'bg-amber-400',   dotGlow: 'shadow-[0_0_8px_rgba(251,191,36,0.8)]',  wrap: 'border-amber-500/15 bg-amber-500/5' },
  stopped: { label: '중단', dotCls: 'bg-red-400',     dotGlow: 'shadow-[0_0_8px_rgba(248,113,113,0.8)]', wrap: 'border-red-500/15 bg-red-500/5' },
}

function SystemStatusBar({ status }: { status: SysStatus | null }) {
  if (!status) return (
    <div className="rounded-2xl border border-zinc-800 p-4 mb-6 shimmer h-16" />
  )
  const oc = OVERALL_CFG[status.overall]

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={SPRING}
      className={`rounded-2xl border p-4 mb-6 ${oc.wrap}`}
    >
      <div className="flex flex-wrap gap-x-6 gap-y-3 items-center">
        <div className="flex items-center gap-2.5">
          <span className="relative flex">
            <motion.span
              className={`w-2.5 h-2.5 rounded-full ${oc.dotCls} ${oc.dotGlow}`}
              animate={{ scale: [1, 1.3, 1], opacity: [1, 0.6, 1] }}
              transition={{ repeat: Infinity, duration: 2.5, ease: 'easeInOut' }}
            />
          </span>
          <span className="font-semibold text-base tracking-tight">
            시스템 <span className={
              status.overall === 'normal'  ? 'text-emerald-400' :
              status.overall === 'warning' ? 'text-amber-400'   : 'text-red-400'
            }>{oc.label}</span>
          </span>
        </div>

        <div className="flex flex-wrap gap-2">
          <StatChip label="활성 인풋" value={`${status.active_count}개`} />
          <StatChip
            label="LLM 잔여"
            value={`${status.llm_remaining}회`}
            warn={status.llm_remaining < 10}
          />
          <StatChip
            label="스케줄러"
            value={status.scheduler.running ? '동작 중' : '중단'}
            ok={status.scheduler.running}
            warn={!status.scheduler.running}
          />
          {status.last_crawl_at && (
            <StatChip label="마지막 크롤링" value={timeAgo(status.last_crawl_at)} />
          )}
        </div>
      </div>
    </motion.div>
  )
}

function StatChip({ label, value, warn, ok }: {
  label: string; value: string; warn?: boolean; ok?: boolean
}) {
  return (
    <span className="text-xs px-2.5 py-1 rounded-lg bg-zinc-900/80 border border-zinc-800 text-zinc-400 flex items-center gap-1.5">
      {label}
      <b className={warn ? 'text-red-400' : ok ? 'text-emerald-400' : 'text-zinc-200'}>
        {value}
      </b>
    </span>
  )
}

// ── JudgmentCard ────────────────────────────────────────────────────────────

function JudgmentCard({ result, onDismiss }: { result: JudgmentResult; onDismiss: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -8, scale: 0.96, transition: { duration: 0.18 } }}
      transition={SPRING}
      className={`mt-5 p-4 rounded-xl border ${
        result.approved
          ? 'bg-emerald-950/30 border-emerald-900/40'
          : 'bg-red-950/30 border-red-900/40'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-2 flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={`text-sm font-semibold ${result.approved ? 'text-emerald-400' : 'text-red-400'}`}>
              {result.approved ? '✓ 승인' : '✗ 거절'}
            </span>
            {result.crawl_method && (
              <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-zinc-800/80 text-zinc-500 border border-zinc-700/50">
                {result.crawl_method}
              </span>
            )}
            {result.approved && result.created_count > 0 && (
              <span className="text-xs text-zinc-500">{result.created_count}개 등록됨</span>
            )}
          </div>
          <p className={`text-sm leading-relaxed ${result.approved ? 'text-emerald-300/80' : 'text-red-300/80'}`}>
            {result.reason}
          </p>
          {result.target_sites.length > 0 && (
            <div className="pt-1 space-y-1">
              {result.target_sites.map(url => (
                <div key={url} className="flex items-center gap-1.5 text-xs text-zinc-400 font-mono truncate">
                  <span className="text-indigo-500 shrink-0">↗</span>
                  <span className="truncate">{url}</span>
                </div>
              ))}
            </div>
          )}
        </div>
        <motion.button
          whileTap={{ scale: 0.9 }}
          onClick={onDismiss}
          className="text-zinc-600 hover:text-zinc-400 transition-colors text-lg leading-none shrink-0 mt-0.5"
        >
          ×
        </motion.button>
      </div>
    </motion.div>
  )
}

// ── InputCard ──────────────────────────────────────────────────────────────

function InputCard({
  input, password, onDelete, onIntervalChange, onCrawl,
}: {
  input: CrawlInput
  password: string
  onDelete: (id: number) => void
  onIntervalChange: (id: number, p: Period) => void
  onCrawl: (id: number) => void
}) {
  const [deleting, setDeleting] = useState(false)
  const [crawling, setCrawling] = useState(false)
  const sc = STATUS_CFG[input.status]

  async function handleDelete() {
    if (!confirm(`"${input.value}" 인풋을 삭제할까요?`)) return
    setDeleting(true)
    try {
      await apiFetch(`/api/inputs/${input.id}`, {
        method: 'DELETE',
        body: JSON.stringify({ password }),
      })
      onDelete(input.id)
    } catch (e: unknown) { alert((e as Error).message) }
    finally { setDeleting(false) }
  }

  async function handlePeriod(p: Period) {
    try {
      await apiFetch(`/api/inputs/${input.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ interval: p, password }),
      })
      onIntervalChange(input.id, p)
    } catch (e: unknown) { alert((e as Error).message) }
  }

  async function handleCrawl() {
    setCrawling(true)
    try {
      await apiFetch(`/api/crawl/${input.id}`, {
        method: 'POST',
        body: JSON.stringify({ password }),
      })
      onCrawl(input.id)
    } catch (e: unknown) { alert((e as Error).message) }
    finally { setCrawling(false) }
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.94, y: -8, transition: { duration: 0.18 } }}
      transition={SPRING}
      whileHover={{ y: -2, transition: { type: 'spring', stiffness: 500, damping: 35 } }}
      className="card-hover bg-zinc-900 rounded-2xl border border-zinc-800 p-5 space-y-4"
    >
      {/* ── header ── */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0 space-y-2">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs px-2 py-0.5 rounded-md bg-zinc-800 text-zinc-500 border border-zinc-700/60 font-mono tracking-wide">
              URL
            </span>

            <span className={`text-xs px-2.5 py-0.5 rounded-full border font-medium flex items-center gap-1.5 ${sc.chip}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${sc.dot}`} />
              {sc.label}
            </span>

            {input.has_new === 1 && (
              <motion.span
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ type: 'spring', stiffness: 500, damping: 20 }}
                className="badge-pulse text-xs px-2.5 py-0.5 rounded-full bg-blue-500 text-white font-bold tracking-wide"
              >
                NEW
              </motion.span>
            )}
          </div>

          <p className="text-base font-medium text-zinc-100 break-all leading-snug">{input.value}</p>
        </div>

        <div className="flex items-center gap-1.5 shrink-0 pt-0.5">
          {(input.status === 'active' || input.status === 'failed') && (
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={handleCrawl}
              disabled={crawling}
              className="text-xs px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border border-zinc-700/60 transition-colors disabled:opacity-40"
            >
              {crawling ? (
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 border border-zinc-500 border-t-zinc-200 rounded-full animate-spin" />
                  실행 중
                </span>
              ) : '수동 크롤링'}
            </motion.button>
          )}
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={handleDelete}
            disabled={deleting}
            className="text-xs px-3 py-1.5 rounded-lg bg-red-950/40 hover:bg-red-900/50 text-red-400 border border-red-900/40 transition-colors disabled:opacity-40"
          >
            {deleting ? '삭제 중' : '삭제'}
          </motion.button>
        </div>
      </div>

      {/* ── Claude judgment ── */}
      <AnimatePresence>
        {input.claude_reason && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className={`text-sm p-3.5 rounded-xl border ${
              input.claude_approved
                ? 'bg-emerald-950/30 border-emerald-900/30 text-emerald-300'
                : 'bg-red-950/30 border-red-900/30 text-red-300'
            }`}
          >
            <span className="font-semibold mr-2 opacity-80">
              {input.claude_approved ? '✓ 승인' : '✗ 거절'}
            </span>
            {input.claude_reason}
            {input.crawl_method && (
              <span className="ml-2 text-xs opacity-50 font-mono">
                [{input.crawl_method}]
              </span>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Stats ── */}
      <div className="flex flex-wrap gap-1">
        <StatPill icon="📄" value={`${input.post_count}개`} label="수집" />
        <StatPill icon="⏱" value={timeAgo(input.last_crawl_at)} label="마지막" />
        {input.next_crawl_at && (
          <StatPill icon="⏰" value={fmtTime(input.next_crawl_at)} label="다음" />
        )}
      </div>

      {/* ── Interval picker ── */}
      <div className="flex items-center gap-2 pt-0.5">
        <span className="text-xs text-zinc-600 shrink-0">주기</span>
        <div className="flex gap-1.5">
          {(['1h', '6h', '24h'] as Period[]).map(p => (
            <motion.button
              key={p}
              whileTap={{ scale: 0.93 }}
              onClick={() => handlePeriod(p)}
              className={`text-xs px-3 py-1 rounded-lg border transition-colors ${
                input.crawl_interval === p
                  ? 'bg-zinc-700 border-zinc-600 text-zinc-100 font-medium'
                  : 'border-zinc-800 text-zinc-600 hover:border-zinc-700 hover:text-zinc-400'
              }`}
            >
              {PERIOD_LABELS[p]}
            </motion.button>
          ))}
        </div>
      </div>
    </motion.div>
  )
}

function StatPill({ icon, value, label }: { icon: string; value: string; label: string }) {
  return (
    <span className="text-xs px-2.5 py-1 rounded-lg bg-zinc-800/60 border border-zinc-800 text-zinc-400 flex items-center gap-1.5 mr-1 mb-1">
      <span className="opacity-40">{icon}</span>
      <span className="opacity-60">{label}</span>
      <b className="text-zinc-200">{value}</b>
    </span>
  )
}

// ── Page ───────────────────────────────────────────────────────────────────

export default function ManagePage() {
  const [unlocked,   setUnlocked]   = useState(false)
  const [password,   setPassword]   = useState('')
  const [pwInput,    setPwInput]    = useState('')

  const [inputs,     setInputs]     = useState<CrawlInput[]>([])
  const [sysStatus,  setSysStatus]  = useState<SysStatus | null>(null)

  const [value,      setValue]      = useState('')
  const [period,     setPeriod]     = useState<Period>('6h')
  const [submitting, setSubmitting] = useState(false)
  const [formError,  setFormError]  = useState('')
  const [lastResult, setLastResult] = useState<JudgmentResult | null>(null)

  useEffect(() => {
    if (!unlocked) return
    loadInputs()
    loadStatus()
    const t = window.setInterval(loadStatus, 15_000)
    return () => window.clearInterval(t)
  }, [unlocked])

  async function loadInputs() {
    try { setInputs(await apiFetch<CrawlInput[]>('/api/inputs')) } catch { /* silent */ }
  }
  async function loadStatus() {
    try { setSysStatus(await apiFetch<SysStatus>('/api/status')) } catch { /* silent */ }
  }

  function unlock() {
    setPassword(pwInput)
    setUnlocked(true)
  }

  async function handleSubmit(e: { preventDefault(): void }) {
    e.preventDefault()
    const trimmed = value.trim()
    if (!trimmed) return
    setFormError('')
    setLastResult(null)
    setSubmitting(true)

    try {
      const res = await apiFetch<{
        approved: boolean
        judgment: { reason: string; crawl_method: string | null; target_sites?: string[] }
        created_count: number
      }>('/api/inputs', {
        method: 'POST',
        body: JSON.stringify({ value: trimmed, password, interval: period }),
      })
      setLastResult({
        value: trimmed,
        approved: res.approved,
        reason: res.judgment.reason,
        crawl_method: res.judgment.crawl_method,
        target_sites: res.judgment.target_sites ?? [],
        created_count: res.created_count,
      })
      setValue('')
      await loadInputs()
      await loadStatus()
    } catch (err: unknown) {
      const e = err as { status?: number; message: string }
      if (e.status === 401) {
        setUnlocked(false); setPassword('')
        setFormError('비밀번호가 틀렸습니다. 다시 로그인하세요.')
      } else {
        setFormError(e.message)
      }
    } finally {
      setSubmitting(false)
    }
  }

  function handleDelete(id: number) { setInputs(prev => prev.filter(i => i.id !== id)) }
  function handlePeriodChange(id: number, p: Period) {
    setInputs(prev => prev.map(i => i.id === id ? { ...i, crawl_interval: p } : i))
  }
  function handleCrawl(id: number) {
    setInputs(prev => prev.map(i => i.id === id ? { ...i, status: 'crawling' as InputStatus } : i))
    window.setTimeout(loadInputs, 3000)
  }

  // ── Password gate ──────────────────────────────────────────────────────

  if (!unlocked) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background: 'radial-gradient(ellipse 80% 60% at 50% 40%, rgba(99,102,241,0.06) 0%, transparent 70%)',
          }}
        />

        <motion.div
          initial={{ opacity: 0, y: 28, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={SPRING}
          className="w-full max-w-sm relative"
        >
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold gradient-text mb-1">crawl-blog</h1>
            <p className="text-zinc-500 text-sm">인풋 관리 · 비밀번호 필요</p>
          </div>

          <div className="gradient-border bg-zinc-900 rounded-2xl p-6 space-y-3">
            <input
              type="password"
              value={pwInput}
              onChange={e => setPwInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && unlock()}
              placeholder="비밀번호 입력"
              autoFocus
              className="input-glow w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-base text-zinc-100 placeholder-zinc-600"
            />
            <motion.button
              whileTap={{ scale: 0.97 }}
              onClick={unlock}
              className="btn-primary w-full rounded-xl py-3 text-base"
            >
              잠금 해제
            </motion.button>
          </div>

          <p className="mt-5 text-center">
            <Link href="/" className="text-sm text-zinc-600 hover:text-zinc-400 transition-colors">← 블로그로 돌아가기</Link>
          </p>
        </motion.div>
      </div>
    )
  }

  // ── Main UI ────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen">
      {/* nav */}
      <div className="border-b border-zinc-900/80 bg-zinc-950/90 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 py-3.5 flex items-center justify-between">
          <Link href="/" className="text-lg font-bold gradient-text">crawl-blog</Link>
          <span className="text-sm text-zinc-500 font-medium">인풋 관리</span>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 py-8 space-y-8">
        {/* system status */}
        <SystemStatusBar status={sysStatus} />

        {/* add form */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...SPRING, delay: 0.05 }}
          className="bg-zinc-900 rounded-2xl border border-zinc-800 p-6"
        >
          <div className="flex items-center gap-2.5 mb-5">
            <span className="w-1 h-5 rounded-full bg-gradient-to-b from-indigo-400 to-cyan-400" />
            <h2 className="text-base font-semibold text-zinc-100">인풋 등록</h2>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              type="text"
              value={value}
              onChange={e => setValue(e.target.value)}
              placeholder="URL 또는 주제를 자유롭게 입력하세요"
              disabled={submitting}
              className="input-glow w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-base text-zinc-100 placeholder-zinc-600 disabled:opacity-50"
            />

            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm text-zinc-500">주기:</span>
              {(['1h', '6h', '24h'] as Period[]).map(p => (
                <motion.button
                  key={p}
                  type="button"
                  whileTap={{ scale: 0.94 }}
                  onClick={() => setPeriod(p)}
                  className={`text-sm px-4 py-1.5 rounded-lg border transition-colors ${
                    period === p
                      ? 'bg-zinc-700 border-zinc-600 text-zinc-100 font-medium'
                      : 'border-zinc-800 text-zinc-500 hover:border-zinc-700 hover:text-zinc-300'
                  }`}
                >
                  {PERIOD_LABELS[p]}
                </motion.button>
              ))}

              <motion.button
                type="submit"
                whileTap={{ scale: 0.97 }}
                disabled={submitting || !value.trim()}
                className="btn-primary ml-auto px-6 py-2 rounded-xl text-sm"
              >
                {submitting ? (
                  <span className="flex items-center gap-2">
                    <span className="w-3.5 h-3.5 border border-white/40 border-t-white rounded-full animate-spin" />
                    판단 중...
                  </span>
                ) : '등록'}
              </motion.button>
            </div>
          </form>

          {/* Judgment result card */}
          <AnimatePresence>
            {lastResult && (
              <JudgmentCard
                result={lastResult}
                onDismiss={() => setLastResult(null)}
              />
            )}
          </AnimatePresence>

          <AnimatePresence>
            {formError && (
              <motion.p
                initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                className="mt-3 text-sm text-red-400 flex items-center gap-2"
              >
                <span className="text-red-500">⚠</span> {formError}
              </motion.p>
            )}
          </AnimatePresence>
        </motion.section>

        {/* input list */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2.5">
              <span className="w-1 h-5 rounded-full bg-gradient-to-b from-indigo-400 to-cyan-400" />
              <h2 className="text-base font-semibold text-zinc-100">
                인풋 목록
                {inputs.length > 0 && (
                  <span className="ml-2 text-sm font-normal text-zinc-600">{inputs.length}개</span>
                )}
              </h2>
            </div>
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={loadInputs}
              className="text-xs text-zinc-600 hover:text-zinc-400 transition-colors px-2 py-1 rounded-lg hover:bg-zinc-900"
            >
              새로고침
            </motion.button>
          </div>

          {inputs.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              className="text-center py-20"
            >
              <p className="text-zinc-600 text-base mb-2">등록된 인풋이 없습니다</p>
              <p className="text-zinc-700 text-sm">위 폼에서 URL을 등록해보세요</p>
            </motion.div>
          ) : (
            <AnimatePresence mode="popLayout">
              {inputs.map((input, i) => (
                <motion.div
                  key={input.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0, transition: { ...SPRING, delay: i * 0.06 } }}
                  className="mb-3"
                >
                  <InputCard
                    input={input}
                    password={password}
                    onDelete={handleDelete}
                    onIntervalChange={handlePeriodChange}
                    onCrawl={handleCrawl}
                  />
                </motion.div>
              ))}
            </AnimatePresence>
          )}
        </section>
      </div>
    </div>
  )
}
