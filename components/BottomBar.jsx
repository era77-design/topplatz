'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState } from 'react'

const LANGS = ['en', 'de', 'nl', 'sv']

export default function BottomBar() {
  const pathname = usePathname()
  const lang = LANGS.find(l => pathname.startsWith(`/${l}`)) || 'en'
  const [moreOpen, setMoreOpen] = useState(false)

  function switchLang(l) {
    const segments = pathname.split('/')
    segments[1] = l
    window.location.href = segments.join('/')
  }

  const iconStyle = { fontSize: '20px', color: 'var(--text)' }
  const labelStyle = { fontSize: '10px', color: 'var(--text-secondary)' }
  const tabStyle = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '3px',
    flex: 1,
    padding: '8px 0',
    textDecoration: 'none',
  }

  return (
    <>
      {/* More sheet */}
      {moreOpen && (
        <div style={{
          position: 'fixed',
          bottom: '60px',
          left: 0,
          right: 0,
          background: 'var(--nav-bg)',
          borderTop: '0.5px solid var(--border)',
          boxShadow: '0 -4px 20px rgba(0,0,0,0.12)',
          padding: '16px',
          zIndex: 99,
        }}>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '10px' }}>Language</p>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
            {LANGS.map(l => (
              <button key={l} onClick={() => switchLang(l)} style={{
                fontSize: '12px',
                padding: '6px 14px',
                borderRadius: '6px',
                border: '0.5px solid var(--border)',
                background: lang === l ? 'var(--text)' : 'transparent',
                color: lang === l ? 'var(--bg)' : 'var(--text-secondary)',
                cursor: 'pointer',
                fontWeight: lang === l ? 500 : 400,
              }}>
                {l.toUpperCase()}
              </button>
            ))}
          </div>

          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>Pages</p>
          {[
            { href: `/${lang}/about`,   icon: 'ℹ️', label: 'About' },
            { href: `/${lang}/contact`, icon: '✉️', label: 'Contact' },
            { href: `/${lang}/privacy`, icon: '🔒', label: 'Privacy Policy' },
          ].map(item => (
            <Link key={item.href} href={item.href} onClick={() => setMoreOpen(false)} style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '13px 0',
              borderBottom: '0.5px solid var(--border)',
              fontSize: '15px',
              color: 'var(--text)',
              textDecoration: 'none',
            }}>
              <span style={{ fontSize: '18px', width: '24px', textAlign: 'center' }}>{item.icon}</span>
              <span>{item.label}</span>
              <span style={{ marginLeft: 'auto', color: 'var(--text-secondary)', fontSize: '18px' }}>›</span>
            </Link>
          ))}
        </div>
      )}

      {/* Bottom tab bar */}
      <nav className="bottom-bar" style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        height: '60px',
        background: 'var(--nav-bg)',
        borderTop: '0.5px solid var(--border)',
        boxShadow: '0 -4px 12px rgba(0,0,0,0.08)',
        display: 'flex',
        justifyContent: 'space-around',
        alignItems: 'center',
        zIndex: 100,
      }}>
        {[
          { href: `/${lang}`,            icon: '🏠', label: 'Home' },
          { href: `/${lang}/search`,     icon: '🔍', label: 'Search' },
          { href: `/${lang}/categories`, icon: '📂', label: 'Categories' },
        ].map(item => (
          <Link key={item.href} href={item.href} style={tabStyle}>
            <span style={iconStyle}>{item.icon}</span>
            <span style={labelStyle}>{item.label}</span>
          </Link>
        ))}

        <button onClick={() => setMoreOpen(!moreOpen)} style={{
          ...tabStyle,
          background: 'none',
          border: 'none',
          cursor: 'pointer',
        }}>
          <span style={{ fontSize: '22px', color: 'var(--text)', lineHeight: 1 }}>
            {moreOpen ? '✕' : '☰'}
          </span>
          <span style={labelStyle}>More</span>
        </button>
      </nav>

      <style>{`
        @media (min-width: 641px) {
          .bottom-bar { display: none !important; }
        }
      `}</style>
    </>
  )
}
