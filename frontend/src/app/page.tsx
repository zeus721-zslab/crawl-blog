'use client'
import { useState, useEffect, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { apiFetch } from '@/lib/api'

interface Post {
  id: number
  input_id: number
  title: string
  content: string
  summary: string
  tags: string[]
  source_url: string | null
  is_read: number
  is_new: number
  created_at: string
}

interface CrawlInput {
  id: number
  value: string
  type: 'keyword' | 'url'
  post_count: number
}

interface PostsResponse {
  total: number
  page: number
  per_page: number
  posts: Post[]
}

const SPRING = { type: 'spring', stiffness: 380, damping: 32 } as const
const PER_PAGE = 20

function timeAgo(iso: string): string {
  const d = new Date(iso.includes('Z') || iso.includes('+') ? iso : iso + 'Z')
  const min = Math.floor((Date.now() - d.getTime()) / 60000)
  if (min < 1)  return '방금 전'
  if (min < 60) return `${min}분 전`
  const hr = Math.floor(min / 60)
  if (hr < 24)  return `${hr}시간 전`
  return `${Math.floor(hr / 24)}일 전`
}

// ── Skeleton ───────────────────────────────────────────────────────────────

function PostSkeleton() {
  return (
    <div className="bg-zinc-900 rounded-2xl border border-zinc-800 p-5 space-y-3">
      <div className="flex justify-between">
        <div className="shimmer h-4 w-3/5 rounded-lg" />
        <div className="shimmer h-4 w-10 rounded-full" />
      </div>
      <div className="shimmer h-3 w-full rounded-lg" />
      <div className="shimmer h-3 w-4/5 rounded-lg" />
      <div className="flex gap-1.5">
        <div className="shimmer h-5 w-14 rounded-full" />
        <div className="shimmer h-5 w-16 rounded-full" />
        <div className="shimmer h-5 w-12 rounded-full" />
      </div>
    </div>
  )
}

// ── PostCard ───────────────────────────────────────────────────────────────

function PostCard({ post, onClick }: { post: Post; onClick: () => void }) {
  return (
    <motion.article
      layout
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.97, transition: { duration: 0.15 } }}
      transition={SPRING}
      whileHover={{ y: -3, transition: { type: 'spring', stiffness: 500, damping: 35 } }}
      onClick={onClick}
      className={`card-hover bg-zinc-900 rounded-2xl border border-zinc-800 p-5 cursor-pointer ${
        post.is_read ? 'opacity-55' : ''
      }`}
    >
      {/* title row */}
      <div className="flex items-start justify-between gap-3 mb-2.5">
        <h2 className="text-base font-semibold text-zinc-100 leading-snug">
          {post.title}
        </h2>
        {post.is_new === 1 && (
          <motion.span
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ type: 'spring', stiffness: 500, damping: 22 }}
            className="badge-pulse shrink-0 text-xs px-2.5 py-0.5 rounded-full bg-blue-500 text-white font-bold tracking-wide"
          >
            NEW
          </motion.span>
        )}
      </div>

      {/* summary */}
      {post.summary && (
        <p className="text-sm text-zinc-400 leading-relaxed mb-3 line-clamp-2">
          {post.summary}
        </p>
      )}

      {/* tags */}
      {post.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {post.tags.slice(0, 4).map((t, i) => (
            <span
              key={t}
              className={`text-xs px-2 py-0.5 rounded-full border ${
                i === 0
                  ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
                  : 'bg-zinc-800/80 text-zinc-500 border-zinc-700/60'
              }`}
            >
              {t}
            </span>
          ))}
        </div>
      )}

      {/* footer */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-zinc-600">{timeAgo(post.created_at)}</span>
        {post.is_read === 1 && (
          <span className="text-xs text-zinc-700">읽음</span>
        )}
      </div>
    </motion.article>
  )
}

// ── TabBtn ─────────────────────────────────────────────────────────────────

function TabBtn({ active, onClick, children }: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <motion.button
      onClick={onClick}
      whileTap={{ scale: 0.94 }}
      className={`relative text-sm px-3 py-1 rounded-lg transition-colors shrink-0 flex items-center gap-1 ${
        active
          ? 'bg-zinc-800 text-zinc-100 font-medium tab-active'
          : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900'
      }`}
    >
      {children}
    </motion.button>
  )
}

// ── Page ───────────────────────────────────────────────────────────────────

export default function HomePage() {
  const [posts,       setPosts]       = useState<Post[]>([])
  const [inputs,      setInputs]      = useState<CrawlInput[]>([])
  const [total,       setTotal]       = useState(0)
  const [page,        setPage]        = useState(1)
  const [loading,     setLoading]     = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [searchVal,   setSearchVal]   = useState('')
  const [search,      setSearch]      = useState('')
  const [activeTab,   setActiveTab]   = useState<number | null>(null)

  const searchRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    apiFetch<CrawlInput[]>('/api/inputs').then(setInputs).catch(() => {})
  }, [])

  const fetchPosts = useCallback(async (p: number, q: string, inputId: number | null) => {
    const params = new URLSearchParams({ page: String(p), per_page: String(PER_PAGE) })
    if (q)              params.set('search',   q)
    if (inputId !== null) params.set('input_id', String(inputId))
    return apiFetch<PostsResponse>(`/api/posts?${params}`)
  }, [])

  useEffect(() => {
    setLoading(true)
    fetchPosts(1, search, activeTab)
      .then(data => { setPosts(data.posts); setTotal(data.total); setPage(1) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [search, activeTab, fetchPosts])

  async function loadMore() {
    setLoadingMore(true)
    try {
      const next = page + 1
      const data = await fetchPosts(next, search, activeTab)
      setPosts(prev => [...prev, ...data.posts])
      setPage(next)
    } finally {
      setLoadingMore(false)
    }
  }

  function submitSearch(e: { preventDefault(): void }) {
    e.preventDefault()
    setSearch(searchVal)
  }

  function clearSearch() {
    setSearchVal('')
    setSearch('')
  }

  async function openPost(post: Post) {
    if (!post.is_read) {
      apiFetch(`/api/posts/${post.id}/read`, { method: 'PATCH' }).catch(() => {})
      setPosts(prev => prev.map(p => p.id === post.id ? { ...p, is_read: 1, is_new: 0 } : p))
    }
    window.location.href = `/posts/${post.id}`
  }

  const hasMore = posts.length < total

  return (
    <div className="min-h-screen">
      {/* ── sticky header ── */}
      <div className="border-b border-zinc-900/80 sticky top-0 bg-zinc-950/90 backdrop-blur-sm z-10">
        <div className="max-w-3xl mx-auto px-4 py-3.5 flex items-center gap-3">
          <h1 className="text-lg font-bold gradient-text shrink-0">crawl-blog</h1>

          <form onSubmit={submitSearch} className="flex-1 relative max-w-xs">
            <input
              ref={searchRef}
              type="text"
              value={searchVal}
              onChange={e => setSearchVal(e.target.value)}
              placeholder="검색..."
              className="input-glow w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-sm text-zinc-100 placeholder-zinc-600 pr-7"
            />
            <AnimatePresence>
              {searchVal && (
                <motion.button
                  type="button"
                  onClick={clearSearch}
                  initial={{ opacity: 0, scale: 0.7 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.7 }}
                  transition={{ duration: 0.1 }}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-600 hover:text-zinc-400 text-base leading-none w-4 h-4 flex items-center justify-center"
                >
                  ×
                </motion.button>
              )}
            </AnimatePresence>
          </form>

          <a
            href="/manage"
            className="ml-auto text-sm text-zinc-500 hover:text-zinc-300 transition-colors shrink-0 px-2 py-1 rounded-lg hover:bg-zinc-900"
          >
            관리
          </a>
        </div>

        {/* ── tabs ── */}
        {inputs.length > 0 && (
          <div className="max-w-3xl mx-auto px-4 pb-3 flex gap-1 overflow-x-auto scrollbar-none">
            <TabBtn active={activeTab === null} onClick={() => setActiveTab(null)}>
              전체
              {total > 0 && (
                <span className="text-xs text-zinc-500 ml-0.5">{total}</span>
              )}
            </TabBtn>
            {inputs.map(inp => (
              <TabBtn key={inp.id} active={activeTab === inp.id} onClick={() => setActiveTab(inp.id)}>
                <span className="max-w-[96px] truncate">{inp.value}</span>
                {inp.post_count > 0 && (
                  <span className="text-xs text-zinc-600">{inp.post_count}</span>
                )}
              </TabBtn>
            ))}
          </div>
        )}
      </div>

      {/* ── content ── */}
      <div className="max-w-3xl mx-auto px-4 py-6">
        <AnimatePresence>
          {search && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="overflow-hidden mb-4"
            >
              <div className="flex items-center gap-2 text-sm pb-1">
                <span className="text-zinc-500">검색:</span>
                <span className="text-zinc-300 font-medium">"{search}"</span>
                <button
                  onClick={clearSearch}
                  className="text-zinc-600 hover:text-zinc-400 text-xs ml-1 transition-colors"
                >
                  지우기
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {loading ? (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="space-y-3"
          >
            {[...Array(5)].map((_, i) => (
              <PostSkeleton key={i} />
            ))}
          </motion.div>
        ) : posts.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={SPRING}
            className="text-center py-28"
          >
            <p className="text-zinc-600 text-base mb-3">
              {search ? `"${search}" 검색 결과가 없습니다` : '수집된 글이 없습니다'}
            </p>
            {!search && (
              <a
                href="/manage"
                className="inline-flex items-center gap-1.5 text-sm px-4 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-zinc-400 hover:border-zinc-700 hover:text-zinc-300 transition-colors"
              >
                인풋 등록하러 가기 →
              </a>
            )}
          </motion.div>
        ) : (
          <>
            <motion.div
              className="space-y-3"
              initial="hidden"
              animate="visible"
              variants={{ visible: { transition: { staggerChildren: 0.05 } } }}
            >
              <AnimatePresence mode="popLayout">
                {posts.map(post => (
                  <PostCard key={post.id} post={post} onClick={() => openPost(post)} />
                ))}
              </AnimatePresence>
            </motion.div>

            {hasMore && (
              <motion.div
                initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                className="mt-8 text-center"
              >
                <motion.button
                  whileTap={{ scale: 0.97 }}
                  onClick={loadMore}
                  disabled={loadingMore}
                  className="px-8 py-2.5 bg-zinc-900 border border-zinc-800 rounded-xl text-sm text-zinc-400 hover:border-zinc-700 hover:text-zinc-300 transition-colors disabled:opacity-40 font-medium"
                >
                  {loadingMore ? (
                    <span className="flex items-center gap-2">
                      <span className="w-3.5 h-3.5 border border-zinc-600 border-t-zinc-300 rounded-full animate-spin" />
                      로딩 중
                    </span>
                  ) : (
                    `더 보기 · ${total - posts.length}개 남음`
                  )}
                </motion.button>
              </motion.div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
