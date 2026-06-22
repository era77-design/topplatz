'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import articlesData from '@/data/articles-meta.json'

const LANGS = ['en', 'de', 'nl', 'sv']
const STATIC_ROUTES = ['about', 'contact', 'privacy', 'categories', 'category', 'impressum']

export default function Navbar() {
  const pathname = usePathname()
  const lang = LANGS.find(l => pathname.startsWith(`/${l}`)) || 'en'
  const [theme, setTheme] = useState('light')

  useEffect(() => {
    const t = localStorage.getItem('theme') || 'light'
    setTheme(t)
  }, [])

  function toggleTheme() {
    const next = theme === 'light' ? 'dark' : 'light'
    setTheme(next)
    localStorage.setItem('theme', next)
    document.documentElement.setAttribute('data-theme', next)
  }

  function switchLang(l) {
    const segments = pathname.split('/')
    const second = segments[2]

    // Главная, /about, /contact, /privacy, /categories, /category/[cat] —
    // эти пути одинаковы на всех языках, просто меняем сегмент языка.
    if (!second || STATIC_ROUTES.includes(second)) {
      segments[1] = l
      window.location.href = segments.join('/')
      return
    }

    // Иначе это страница статьи — её slug сгенерирован независимо для
    // каждого языка и почти наверняка НЕ существует в другом языке.
    // Ищем категорию этой статьи и переходим в категорию на новом языке,
    // а если не нашли — на главную (вместо 404 на угаданном slug).
    const article = (articlesData[lang] || []).find(a => a.slug === second)
    window.location.href = article?.category
      ? `/${l}/category/${article.category}`
      : `/${l}`
  }

  return (
    <>
      <nav style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '12px 24px', borderBottom: '0.5px solid var(--border)',
        background: 'var(--nav-bg)', position: 'sticky', top: 0, zIndex: 100,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
          <Link href={`/${lang}`} style={{ fontSize: '18px', fontWeight: 500 }}>
            TopPlatz
          </Link>
          <div className="desktop-links" style={{ display: 'flex', gap: '20px' }}>
            <Link href={`/${lang}`} style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Home</Link>
            <Link href={`/${lang}/about`} style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>About</Link>
            <Link href={`/${lang}/contact`} style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Contact</Link>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {LANGS.map(l => (
            <button key={l} onClick={() => switchLang(l)} style={{
              fontSize: '11px', padding: '3px 8px', borderRadius: '5px',
              border: '0.5px solid var(--border)',
              background: lang === l ? 'var(--text)' : 'transparent',
              color: lang === l ? 'var(--bg)' : 'var(--text-secondary)',
              cursor: 'pointer', fontWeight: lang === l ? 500 : 400,
            }}>
              {l.toUpperCase()}
            </button>
          ))}
          <div style={{ width: '1px', height: '16px', background: 'var(--border)', margin: '0 4px' }} />
          <button onClick={toggleTheme} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '18px', padding: '2px' }}>
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
        </div>
      </nav>
      <style>{`@media (max-width: 640px) { .desktop-links { display: none !important; } }`}</style>
    </>
  )
}
