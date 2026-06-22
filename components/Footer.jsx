'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const LANGS = ['en', 'de', 'nl', 'sv']

const LABELS = {
  en: { categories: 'Categories', impressum: 'Legal Notice', privacy: 'Privacy', about: 'About', contact: 'Contact', sitemap: 'Sitemap' },
  de: { categories: 'Kategorien', impressum: 'Impressum',    privacy: 'Datenschutz', about: 'Über uns', contact: 'Kontakt', sitemap: 'Sitemap' },
  nl: { categories: 'Categorieën', impressum: 'Colofon',     privacy: 'Privacy', about: 'Over ons', contact: 'Contact', sitemap: 'Sitemap' },
  sv: { categories: 'Kategorier', impressum: 'Juridiskt',    privacy: 'Integritet', about: 'Om oss', contact: 'Kontakt', sitemap: 'Sitemap' },
}

export default function Footer() {
  const pathname = usePathname()
  const lang = LANGS.find(l => pathname?.startsWith(`/${l}`)) || 'en'
  const t = LABELS[lang] || LABELS.en

  const linkStyle = {
    fontSize: '12px',
    color: 'var(--text-secondary)',
    textDecoration: 'none',
  }

  return (
    <footer className="site-footer" style={{
      borderTop: '0.5px solid var(--border)',
      padding: '16px 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      flexWrap: 'wrap',
      gap: '12px',
      marginTop: '16px',
    }}>
      <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
        © {new Date().getFullYear()} TopPlatz
      </span>
      <nav style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
        <Link href={`/${lang}/categories`} style={linkStyle}>{t.categories}</Link>
        <Link href={`/${lang}/about`}      style={linkStyle}>{t.about}</Link>
        <Link href={`/${lang}/contact`}    style={linkStyle}>{t.contact}</Link>
        <Link href={`/${lang}/privacy`}    style={linkStyle}>{t.privacy}</Link>
        <Link href={`/${lang}/impressum`}  style={{ ...linkStyle, fontWeight: 500 }}>{t.impressum}</Link>
        <a href="/sitemap.xml" target="_blank" rel="noopener" style={linkStyle}>{t.sitemap}</a>
      </nav>

      {/* Footer только на десктопе — на мобиле навигация в BottomBar */}
      <style>{`
        @media (max-width: 640px) {
          .site-footer { display: none !important; }
        }
      `}</style>
    </footer>
  )
}
