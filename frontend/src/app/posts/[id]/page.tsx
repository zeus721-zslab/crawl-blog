'use client'
import { use, useEffect, useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
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

const SPRING = { type: 'spring', stiffness: 380, damping: 32 } as const

function fmtDate(iso: string): string {
  const d = new Date(iso.includes('Z') || iso.includes('+') ? iso : iso + 'Z')
  return d.toLocaleDateString('ko-KR', {
    year: 'numeric', month: 'long', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

// XSS-safe: escape HTML entities first, then apply markdown patterns
function mdToHtml(md: string): string {
  const e = md
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')

  return e
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm,  '<h2>$1</h2>')
    .replace(/^# (.+)$/gm,   '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,     '<em>$1</em>')
    .replace(/`([^`]+)`/g,     '<code>$1</code>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
    .replace(/^[-*] (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>[\s\S]+?<\/li>)(?=\s*(?!<li>))/g, '<ul>$1</ul>')
    .replace(/\n\n+/g, '</p><p>')
    .replace(/^(?!<[h1-6ulp])(.+)$/gm, '<p>$1</p>')
}

// ── Loading skeleton ────────────────────────────────────────────────────────

function PostLoadingSkeleton() {
  return (
    <div className="min-h-screen">
      <div className="border-b border-zinc-900">
        <div className="max-w-2xl mx-auto px-4 py-4">
          <div className="shimmer h-4 w-20 rounded-lg" />
        </div>
      </div>
      <div className="max-w-2xl mx-auto px-4 py-10 space-y-5">
        <div className="shimmer h-8 w-4/5 rounded-xl" />
        <div className="shimmer h-8 w-3/5 rounded-xl" />
        <div className="space-y-2 mt-4">
          <div className="shimmer h-4 w-full rounded-lg" />
          <div className="shimmer h-4 w-full rounded-lg" />
          <div className="shimmer h-4 w-2/3 rounded-lg" />
        </div>
        <div className="flex gap-2 mt-2">
          <div className="shimmer h-6 w-16 rounded-full" />
          <div className="shimmer h-6 w-20 rounded-full" />
          <div className="shimmer h-6 w-14 rounded-full" />
        </div>
        <div className="shimmer h-3 w-32 rounded-lg mt-4" />
        <div className="border-t border-zinc-900 mt-8 pt-8 space-y-3">
          {[...Array(8)].map((_, i) => (
            <div key={i} className={`shimmer h-4 rounded-lg ${i % 3 === 2 ? 'w-2/3' : 'w-full'}`} />
          ))}
        </div>
      </div>
    </div>
  )
}

// ── Page ───────────────────────────────────────────────────────────────────

export default function PostPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const [post,     setPost]     = useState<Post | null>(null)
  const [loading,  setLoading]  = useState(true)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    apiFetch<Post>(`/api/posts/${id}`)
      .then(data => {
        setPost(data)
        apiFetch(`/api/posts/${id}/read`, { method: 'PATCH' }).catch(() => {})
      })
      .catch((e: { status?: number }) => {
        if (e.status === 404) setNotFound(true)
      })
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <PostLoadingSkeleton />

  if (notFound || !post) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
          transition={SPRING}
          className="text-center space-y-4"
        >
          <p className="text-zinc-500 text-base">글을 찾을 수 없습니다</p>
          <Link
            href="/"
            className="inline-block text-sm px-4 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-zinc-400 hover:border-zinc-700 hover:text-zinc-300 transition-colors"
          >
            ← 목록으로
          </Link>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      {/* nav */}
      <div className="border-b border-zinc-900/80 bg-zinc-950/90 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 py-3.5 flex items-center justify-between">
          <Link href="/" className="text-sm text-zinc-500 hover:text-zinc-300 transition-colors flex items-center gap-1.5">
            <span>←</span> 목록으로
          </Link>
          <span className="gradient-text text-sm font-bold">crawl-blog</span>
        </div>
      </div>

      <motion.article
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={SPRING}
        className="max-w-2xl mx-auto px-4 py-10"
      >
        {/* ── header ── */}
        <header className="mb-10">
          {/* gradient accent bar */}
          <div className="w-10 h-1 rounded-full bg-gradient-to-r from-indigo-400 to-cyan-400 mb-6" />

          <h1 className="text-2xl font-bold text-zinc-100 leading-snug mb-5">
            {post.title}
          </h1>

          {/* summary quote */}
          {post.summary && (
            <div className="relative pl-5 mb-6">
              <span
                className="absolute left-0 top-0 bottom-0 w-0.5 rounded-full"
                style={{ background: 'linear-gradient(180deg,#6366f1,#22d3ee)' }}
              />
              <p className="text-zinc-400 text-base leading-relaxed italic">
                {post.summary}
              </p>
            </div>
          )}

          {/* tags */}
          {post.tags.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-6">
              {post.tags.map((t, i) => (
                <motion.span
                  key={t}
                  initial={{ opacity: 0, scale: 0.85 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ ...SPRING, delay: i * 0.04 }}
                  className={`text-xs px-2.5 py-0.5 rounded-full border ${
                    i === 0
                      ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
                      : 'bg-zinc-800/80 text-zinc-500 border-zinc-700/60'
                  }`}
                >
                  {t}
                </motion.span>
              ))}
            </div>
          )}

          {/* meta */}
          <div className="flex flex-wrap items-center gap-4 text-xs text-zinc-600 border-t border-zinc-900 pt-4">
            <span>{fmtDate(post.created_at)}</span>
            {post.source_url && (
              <a
                href={post.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-zinc-400 transition-colors flex items-center gap-1"
              >
                원문 보기 <span className="text-indigo-500">↗</span>
              </a>
            )}
          </div>
        </header>

        {/* ── content ── */}
        <div
          className="post-content text-zinc-300 text-base leading-relaxed"
          dangerouslySetInnerHTML={{ __html: mdToHtml(post.content) }}
        />

        {/* ── footer ── */}
        <div className="mt-14 pt-6 border-t border-zinc-900">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm text-zinc-500 hover:text-zinc-300 transition-colors group"
          >
            <motion.span
              className="inline-block"
              whileHover={{ x: -3 }}
              transition={{ type: 'spring', stiffness: 500, damping: 30 }}
            >
              ←
            </motion.span>
            목록으로 돌아가기
          </Link>
        </div>
      </motion.article>
    </div>
  )
}
