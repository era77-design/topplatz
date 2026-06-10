'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'

const LANGS = ['en', 'de', 'nl', 'sv']

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
    segments[1] = l
    window.location.href = segments.join('/')
  }

  return (
    <>
      {/* Десктоп навбар */}
      <nav style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 24px',
        borderBottom: '0.5px solid var(--border)',
        background: 'var(--nav-bg)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
          <Link href={`/${lang}`} style={{ fontSize: '18px', fontWeight: 500 }}>
            TopPlatz
          </Link>
          {/* Десктоп ссылки — скрыты на мобиле */}
          <div className="desktop-links" style={{ display: 'flex', gap: '20px' }}>
            <Link href={`/${lang}`} style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Home</Link>
            <Link href={`/${lang}/about`} style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>About</Link>
            <Link href={`/${lang}/contact`} style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Contact</Link>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {/* Языки */}
          {LANGS.map(l => (
            <button key={l} onClick={() => switchLang(l)} style={{
              fontSize: '11px',
              padding: '3px 8px',
              borderRadius: '5px',
              border: '0.5px solid var(--border)',
              background: lang === l ? 'var(--text)' : 'transparent',
              color: lang === l ? 'var(--bg)' : 'var(--text-secondary)',
              cursor: 'pointer',
              fontWeight: lang === l ? 500 : 400,
            }}>
              {l.toUpperCase()}
            </button>
          ))}

          {/* Разделитель */}
          <div style={{ width: '1px', height: '16px', background: 'var(--border)', margin: '0 4px' }} />

          {/* Переключатель темы */}
          <button onClick={toggleTheme} style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontSize: '18px',
            padding: '2px',
          }}>
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
        </div>
      </nav>

      {/* CSS для скрытия десктоп-ссылок на мобиле */}
      <style>{`
        @media (max-width: 640px) {
          .desktop-links { display: none !important; }
        }
      `}</style>
    </>
  )
}