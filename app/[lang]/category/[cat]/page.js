import Link from 'next/link'
import { getArticlesByCategory, CATEGORIES, getCategoryName } from '@/lib/articles'

const LANGS = ['en', 'de', 'nl', 'sv']

export async function generateStaticParams() {
  const params = []
  for (const lang of LANGS) {
    for (const cat of CATEGORIES) {
      params.push({ lang, cat: cat.slug })
    }
  }
  return params
}

export async function generateMetadata({ params }) {
  const { lang, cat } = await params
  const name = getCategoryName(cat, lang)
  return { title: `${name} — TopPlatz` }
}

const LABELS = {
  en: { back: '← All Categories', empty: 'No articles yet in this category.' },
  de: { back: '← Alle Kategorien', empty: 'Noch keine Anleitungen in dieser Kategorie.' },
  nl: { back: '← Alle categorieën', empty: 'Nog geen handleidingen in deze categorie.' },
  sv: { back: '← Alla kategorier', empty: 'Inga guider ännu i den här kategorin.' },
}

function ArticleCard({ article, lang }) {
  return (
    <Link href={`/${lang}/${article.slug}`} style={{ display: 'block', textDecoration: 'none' }}>
      <div style={{
        background: 'var(--card-bg)',
        border: '0.5px solid var(--border)',
        borderRadius: '12px',
        overflow: 'hidden',
      }}>
        {article.photoUrl && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={article.photoUrl}
            alt={article.photoAlt || article.title}
            style={{ width: '100%', height: '160px', objectFit: 'cover', display: 'block' }}
          />
        )}
        <div style={{ padding: '14px' }}>
          <div style={{ display: 'flex', gap: '6px', marginBottom: '8px' }}>
            {article.timeMinutes && (
              <span style={{ fontSize: '11px', color: 'var(--text-secondary)', background: 'var(--bg-secondary)', padding: '2px 8px', borderRadius: '10px', border: '0.5px solid var(--border)' }}>
                ⏱ {article.timeMinutes} min
              </span>
            )}
          </div>
          <h3 style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text)', lineHeight: 1.4, marginBottom: '6px' }}>
            {article.title}
          </h3>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
            {article.description}
          </p>
        </div>
      </div>
    </Link>
  )
}

export default async function CategoryPage({ params }) {
  const { lang, cat } = await params
  const t = LABELS[lang] || LABELS.en
  const articles = getArticlesByCategory(lang, cat)
  const catInfo = CATEGORIES.find(c => c.slug === cat)
  const catName = getCategoryName(cat, lang)

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', padding: '32px 16px' }}>
      <Link href={`/${lang}/categories`} style={{ fontSize: '13px', color: 'var(--text-secondary)', textDecoration: 'none', display: 'inline-block', marginBottom: '16px' }}>
        {t.back}
      </Link>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <span style={{ fontSize: '32px' }}>{catInfo?.icon}</span>
        <h1 style={{ fontSize: '26px', fontWeight: 500 }}>{catName}</h1>
        <span style={{ fontSize: '14px', color: 'var(--text-secondary)', marginLeft: '4px' }}>({articles.length})</span>
      </div>

      {articles.length === 0 ? (
        <p style={{ color: 'var(--text-secondary)' }}>{t.empty}</p>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '14px' }}>
          {articles.map(article => (
            <ArticleCard key={article.slug} article={article} lang={lang} />
          ))}
        </div>
      )}
    </div>
  )
}
