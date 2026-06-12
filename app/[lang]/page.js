import Link from 'next/link'
import { getArticles, CATEGORIES } from '@/lib/articles'

const LANGS = ['en', 'de', 'nl', 'sv']

export async function generateStaticParams() {
  return LANGS.map(lang => ({ lang }))
}

export async function generateMetadata({ params }) {
  const { lang } = await params
  const titles = {
    en: 'TopPlatz — How-To Guides for Everything',
    de: 'TopPlatz — Anleitungen für alles',
    nl: 'TopPlatz — Handleidingen voor alles',
    sv: 'TopPlatz — Guider för allt',
  }
  return { title: titles[lang] || titles.en }
}

const HERO = {
  en: { title: 'Step-by-step guides for everything', sub: 'Simple instructions that actually work', latest: 'Latest Guides', all: 'View all', categories: 'Browse by category' },
  de: { title: 'Schritt-für-Schritt Anleitungen für alles', sub: 'Einfache Anweisungen die wirklich funktionieren', latest: 'Neueste Anleitungen', all: 'Alle anzeigen', categories: 'Nach Kategorie' },
  nl: { title: 'Stap voor stap handleidingen voor alles', sub: 'Eenvoudige instructies die echt werken', latest: 'Laatste handleidingen', all: 'Alles bekijken', categories: 'Blader per categorie' },
  sv: { title: 'Steg-för-steg guider för allt', sub: 'Enkla instruktioner som faktiskt fungerar', latest: 'Senaste guider', all: 'Visa alla', categories: 'Bläddra efter kategori' },
}

function ArticleCard({ article, lang }) {
  return (
    <Link href={`/${lang}/${article.slug}`} style={{ display: 'block', textDecoration: 'none' }}>
      <div style={{
        background: 'var(--card-bg)',
        border: '0.5px solid var(--border)',
        borderRadius: '12px',
        overflow: 'hidden',
        transition: 'border-color 0.15s',
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
            {article.difficulty && (
              <span style={{ fontSize: '11px', color: 'var(--text-secondary)', background: 'var(--bg-secondary)', padding: '2px 8px', borderRadius: '10px', border: '0.5px solid var(--border)' }}>
                {article.difficulty}
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

export default async function HomePage({ params }) {
  const { lang } = await params
  const t = HERO[lang] || HERO.en
  const articles = getArticles(lang)
  const latest = articles.slice(0, 8)

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', padding: '0 16px 32px' }}>

      {/* Hero */}
      <div style={{ padding: '32px 0 24px' }}>
        <h1 style={{ fontSize: 'clamp(22px, 4vw, 32px)', fontWeight: 500, marginBottom: '8px', lineHeight: 1.3 }}>
          {t.title}
        </h1>
        <p style={{ fontSize: '15px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          {t.sub}
        </p>
      </div>

      {/* Категории */}
      <div style={{ marginBottom: '36px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 500 }}>{t.categories}</h2>
          <Link href={`/${lang}/categories`} style={{ fontSize: '13px', color: 'var(--text-secondary)', textDecoration: 'none' }}>
            {t.all} →
          </Link>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '10px' }}>
          {CATEGORIES.filter(c => c.slug !== 'general').map(cat => (
            <Link key={cat.slug} href={`/${lang}/category/${cat.slug}`} style={{ textDecoration: 'none' }}>
              <div style={{
                background: 'var(--card-bg)',
                border: '0.5px solid var(--border)',
                borderRadius: '12px',
                padding: '14px',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
              }}>
                <span style={{ fontSize: '22px' }}>{cat.icon}</span>
                <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text)' }}>{cat[lang] || cat.en}</span>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Последние статьи */}
      {latest.length > 0 && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 500 }}>{t.latest}</h2>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '14px' }}>
            {latest.map(article => (
              <ArticleCard key={article.slug} article={article} lang={lang} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
