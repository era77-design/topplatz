export const runtime = 'edge'

import Link from 'next/link'
import articlesData from '@/data/articles-meta.json'

const CATEGORIES = [
  { slug: 'home-garden',  icon: '🏠', en: 'Home & Garden',  de: 'Haus & Garten',    nl: 'Huis & Tuin',      sv: 'Hem & Trädgård' },
  { slug: 'kitchen-food', icon: '🍳', en: 'Kitchen & Food', de: 'Küche & Essen',    nl: 'Keuken & Eten',    sv: 'Kök & Mat' },
  { slug: 'tech-devices', icon: '💻', en: 'Tech & Devices', de: 'Technik & Geräte', nl: 'Tech & Apparaten', sv: 'Teknik & Enheter' },
  { slug: 'diy-crafts',   icon: '✂️', en: 'DIY & Crafts',   de: 'Heimwerken',       nl: 'Knutselen',        sv: 'Gör det själv' },
  { slug: 'general',      icon: '📖', en: 'General',        de: 'Allgemein',        nl: 'Algemeen',         sv: 'Allmänt' },
]
const LABELS = {
  en: { title: 'All Categories', articles: 'articles', home: 'Home' },
  de: { title: 'Alle Kategorien', articles: 'Anleitungen', home: 'Startseite' },
  nl: { title: 'Alle categorieën', articles: 'handleidingen', home: 'Home' },
  sv: { title: 'Alla kategorier', articles: 'guider', home: 'Hem' },
}

export async function generateMetadata({ params }) {
  const { lang } = await params
  const t = LABELS[lang] || LABELS.en
  return { title: `${t.title} — TopPlatz` }
}

export default async function CategoriesPage({ params }) {
  const { lang } = await params
  const t = LABELS[lang] || LABELS.en
  const articles = articlesData[lang] || []
  const counts = {}
  for (const a of articles) counts[a.category] = (counts[a.category] || 0) + 1

  return (
    <div style={{ maxWidth: '760px', margin: '0 auto', padding: '32px 16px' }}>
      <nav style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '20px' }}>
        <Link href={`/${lang}`} style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>{t.home}</Link>
        <span style={{ margin: '0 6px' }}>›</span>
        <span>{t.title}</span>
      </nav>
      <h1 style={{ fontSize: '26px', fontWeight: 500, marginBottom: '24px' }}>{t.title}</h1>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
        {CATEGORIES.map(cat => (
          <Link key={cat.slug} href={`/${lang}/category/${cat.slug}`} style={{ textDecoration: 'none' }}>
            <div style={{ background: 'var(--card-bg)', border: '0.5px solid var(--border)', borderRadius: '12px', padding: '20px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <span style={{ fontSize: '28px' }}>{cat.icon}</span>
              <h2 style={{ fontSize: '15px', fontWeight: 500, color: 'var(--text)', margin: 0 }}>{cat[lang] || cat.en}</h2>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: 0 }}>{counts[cat.slug] || 0} {t.articles}</p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
