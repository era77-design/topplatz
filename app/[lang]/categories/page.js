import Link from 'next/link'
import { getArticles, CATEGORIES, detectCategory } from '@/lib/articles'

const LANGS = ['en', 'de', 'nl', 'sv']

export async function generateStaticParams() {
  return LANGS.map(lang => ({ lang }))
}

const LABELS = {
  en: { title: 'All Categories', articles: 'articles' },
  de: { title: 'Alle Kategorien', articles: 'Anleitungen' },
  nl: { title: 'Alle categorieën', articles: 'handleidingen' },
  sv: { title: 'Alla kategorier', articles: 'guider' },
}

export default async function CategoriesPage({ params }) {
  const { lang } = await params
  const t = LABELS[lang] || LABELS.en
  const articles = getArticles(lang)

  const categoryCounts = {}
  for (const article of articles) {
    const cat = article.category || detectCategory(article.keyword, article.slug)
    categoryCounts[cat] = (categoryCounts[cat] || 0) + 1
  }

  return (
    <div style={{ maxWidth: '760px', margin: '0 auto', padding: '32px 16px' }}>
      <h1 style={{ fontSize: '26px', fontWeight: 500, marginBottom: '24px' }}>{t.title}</h1>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
        {CATEGORIES.map(cat => {
          const count = categoryCounts[cat.slug] || 0
          return (
            <Link key={cat.slug} href={`/${lang}/category/${cat.slug}`} style={{ textDecoration: 'none' }}>
              <div style={{
                background: 'var(--card-bg)',
                border: '0.5px solid var(--border)',
                borderRadius: '12px',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}>
                <span style={{ fontSize: '28px' }}>{cat.icon}</span>
                <h2 style={{ fontSize: '15px', fontWeight: 500, color: 'var(--text)' }}>{cat[lang] || cat.en}</h2>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  {count} {t.articles}
                </p>
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
