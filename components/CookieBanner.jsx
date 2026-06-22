'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const LANGS = ['en', 'de', 'nl', 'sv']

const TEXT = {
  en: {
    msg: 'We use cookies for analytics and personalized ads.',
    privacy: 'Privacy Policy',
    accept: 'Accept',
    decline: 'Decline',
  },
  de: {
    msg: 'Wir verwenden Cookies für Analysen und personalisierte Werbung.',
    privacy: 'Datenschutz',
    accept: 'Akzeptieren',
    decline: 'Ablehnen',
  },
  nl: {
    msg: 'We gebruiken cookies voor analyses en gepersonaliseerde advertenties.',
    privacy: 'Privacybeleid',
    accept: 'Accepteren',
    decline: 'Weigeren',
  },
  sv: {
    msg: 'Vi använder cookies för analys och personliga annonser.',
    privacy: 'Integritetspolicy',
    accept: 'Acceptera',
    decline: 'Avböj',
  },
}

function loadAdSense() {
  if (typeof window === 'undefined') return
  if (document.getElementById('adsense-script')) return
  const s = document.createElement('script')
  s.id = 'adsense-script'
  s.async = true
  s.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3466093106724998'
  s.crossOrigin = 'anonymous'
  document.head.appendChild(s)
}

export default function CookieBanner() {
  const pathname = usePathname()
  const lang = LANGS.find(l => pathname?.startsWith(`/${l}`)) || 'en'
  const t = TEXT[lang] || TEXT.en

  const [show, setShow] = useState(false)

  useEffect(() => {
    try {
      const consent = localStorage.getItem('cookie_consent')
      if (!consent) {
        setShow(true)
      } else if (consent === 'accepted') {
        loadAdSense()
      }
    } catch {}
  }, [])

  function accept() {
    try { localStorage.setItem('cookie_consent', 'accepted') } catch {}
    setShow(false)
    loadAdSense()
  }

  function decline() {
    try { localStorage.setItem('cookie_consent', 'declined') } catch {}
    setShow(false)
  }

  if (!show) return null

  return (
    <>
      <div className="cookie-banner" style={{
        position: 'fixed',
        bottom: 'calc(60px + env(safe-area-inset-bottom, 0px))',
        left: 0,
        right: 0,
        background: 'var(--nav-bg)',
        borderTop: '0.5px solid var(--border)',
        boxShadow: '0 -4px 16px rgba(0,0,0,0.08)',
        padding: '14px 20px',
        zIndex: 150,
        display: 'flex',
        gap: '12px',
        alignItems: 'center',
        flexWrap: 'wrap',
      }}>
        <p style={{
          flex: 1,
          fontSize: '13px',
          color: 'var(--text-secondary)',
          margin: 0,
          lineHeight: 1.5,
          minWidth: '180px',
        }}>
          {t.msg}{' '}
          <Link href={`/${lang}/privacy`} style={{ color: 'var(--text)', textDecoration: 'underline' }}>
            {t.privacy}
          </Link>
        </p>
        <div style={{ display: 'flex', gap: '8px', flexShrink: 0 }}>
          <button onClick={decline} style={{
            padding: '8px 16px',
            borderRadius: '8px',
            fontSize: '13px',
            border: '0.5px solid var(--border)',
            background: 'transparent',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            fontWeight: 400,
          }}>
            {t.decline}
          </button>
          <button onClick={accept} style={{
            padding: '8px 18px',
            borderRadius: '8px',
            fontSize: '13px',
            border: 'none',
            background: 'var(--text)',
            color: 'var(--bg)',
            cursor: 'pointer',
            fontWeight: 500,
          }}>
            {t.accept}
          </button>
        </div>
      </div>
      {/* На десктопе (нет BottomBar) баннер прижат к низу экрана */}
      <style>{`
        @media (min-width: 641px) {
          .cookie-banner {
            bottom: 0 !important;
          }
        }
      `}</style>
    </>
  )
}
