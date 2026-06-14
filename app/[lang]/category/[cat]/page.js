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
  en: { back: '← All Categories', empty: 'No articles yet.', home: 'Home', cats: 'Categories' },
  de: { back: '← Alle Kategorien', empty: 'Noch keine Anleitungen.', home: 'Startseite', cats: 'Kategorien' },
  nl: { back: '← Alle categorieën', empty: 'Nog geen handleidingen.', home: 'Home', cats: 'Categorieën' },
  sv: { back: '← Alla kategorier', empty: 'Inga guider ännu.', home: 'Hem', cats: 'Kategorier' },
}

export async function generateMetadata({ params }) {
  const { lang, cat } = await params
  const catInfo = CATEGORIES.find(c => c.slug === cat) || CATEGORIES[4]
  return { title: `${catInfo[lang] || catInfo.en} — TopPlatz` }
}

export default async function CategoryPage({ params }) {
  const { lang, cat } = await params
  const t = LABELS[lang] || LABELS.en
  const catInfo = CATEGORIES.find(c => c.slug === cat) || CATEGORIES[4]
  const catName = catInfo[lang] || catInfo.en
  const articles = (articlesData[lang] || []).filter(a => a.category === cat)

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', padding: '32px 16px' }}>
      <nav style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '20px', display: 'flex', gap: '6px', alignItems: 'center' }}>
        <Link href={`/${lang}`} style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>{t.home}</Link>
        <span>›</span>
        <Link href={`/${lang}/categories`} style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>{t.cats}</Link>
        <span>›</span>
        <span>{catName}</span>
      </nav>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <span style={{ fontSize: '32px' }}>{catInfo.icon}</span>
        <h1 style={{ fontSize: '26px', fontWeight: 500, margin: 0 }}>{catName}</h1>
        <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>({articles.length})</span>
      </div>

      {articles.length === 0 ? (
        <p style={{ color: 'var(--text-secondary)' }}>{t.empty}</p>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '14px' }}>
          {articles.map(article => (
            <Link key={article.slug} href={`/${lang}/${article.slug}`} style={{ display: 'block', textDecoration: 'none' }}>
              <div style={{ background: 'var(--card-bg)', border: '0.5px solid var(--border)', borderRadius: '12px', overflow: 'hidden' }}>
                {article.photoUrl && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={article.photoUrl} alt={article.photoAlt || article.title} style={{ width: '100%', height: '160px', objectFit: 'cover', display: 'block' }} />
                )}
                <div style={{ padding: '14px' }}>
                  {article.timeMinutes && (
                    <span style={{ fontSize: '11px', color: 'var(--text-secondary)', background: 'var(--bg-secondary)', padding: '2px 8px', borderRadius: '10px', border: '0.5px solid var(--border)', display: 'inline-block', marginBottom: '8px' }}>
                      ⏱ {article.timeMinutes} min
                    </span>
                  )}
                  <h3 style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text)', lineHeight: 1.4, margin: 0 }}>{article.title}</h3>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
