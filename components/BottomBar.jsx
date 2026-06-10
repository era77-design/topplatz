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
          padding: '16px',
          zIndex: 99,
        }}>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '10px' }}>Language</p>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
            {LANGS.map(l => (
              <button key={l} onClick={() => switchLang(l)} style={{
                fontSize: '12px',
                padding: '5px 12px',
                borderRadius: '6px',
                border: '0.5px solid var(--border)',
                background: lang === l ? 'var(--text)' : 'transparent',
                color: lang === l ? 'var(--bg)' : 'var(--text-secondary)',
                cursor: 'pointer',
              }}>
                {l.toUpperCase()}
              </button>
            ))}
          </div>

          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '10px' }}>Pages</p>
          {[
            { href: `/${lang}/about`, icon: 'ℹ️', label: 'About' },
            { href: `/${lang}/contact`, icon: '✉️', label: 'Contact' },
            { href: `/${lang}/privacy`, icon: '🔒', label: 'Privacy Policy' },
          ].map(item => (
            <Link key={item.href} href={item.href} onClick={() => setMoreOpen(false)} style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '12px 0',
              borderBottom: '0.5px solid var(--border)',
              fontSize: '15px',
            }}>
              <span>{item.icon}</span>
              <span>{item.label}</span>
              <span style={{ marginLeft: 'auto', color: 'var(--text-secondary)' }}>›</span>
            </Link>
          ))}
        </div>
      )}

      {/* Bottom tab bar — только на мобиле */}
      <nav className="bottom-bar" style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        height: '60px',
        background: 'var(--nav-bg)',
        borderTop: '0.5px solid var(--border)',
        display: 'flex',
        justifyContent: 'space-around',
        alignItems: 'center',
        zIndex: 100,
      }}>
        {[
          { href: `/${lang}`, icon: '🏠', label: 'Home' },
          { href: `/${lang}/search`, icon: '🔍', label: 'Search' },
          { href: `/${lang}/categories`, icon: '📂', label: 'Categories' },
        ].map(item => (
          <Link key={item.href} href={item.href} style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '3px',
            flex: 1,
            padding: '8px 0',
          }}>
            <span style={{ fontSize: '20px' }}>{item.icon}</span>
            <span style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>{item.label}</span>
          </Link>
        ))}

        <button onClick={() => setMoreOpen(!moreOpen)} style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '3px',
          flex: 1,
          padding: '8px 0',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
        }}>
          <span style={{ fontSize: '20px' }}>{moreOpen ? '✕' : '☰'}</span>
          <span style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>More</span>
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