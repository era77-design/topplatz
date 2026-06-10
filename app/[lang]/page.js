export const runtime = 'edge'
import Link from 'next/link'

const CATEGORIES = [
  { icon: '🏠', slug: 'home-garden',  en: 'Home & Garden',  de: 'Haus & Garten',    nl: 'Huis & Tuin',      sv: 'Hem & Trädgård',  desc: { en: 'Fix, build and grow', de: 'Reparieren und bauen', nl: 'Repareren en bouwen', sv: 'Fixa och bygga' } },
  { icon: '🍳', slug: 'kitchen-food', en: 'Kitchen & Food', de: 'Küche & Essen',    nl: 'Keuken & Eten',    sv: 'Kök & Mat',       desc: { en: 'Cook and prepare',    de: 'Kochen und zubereiten', nl: 'Koken en bereiden', sv: 'Laga och förbereda' } },
  { icon: '💻', slug: 'tech-devices', en: 'Tech & Devices', de: 'Technik & Geräte', nl: 'Tech & Apparaten', sv: 'Teknik & Enheter', desc: { en: 'Setup and fix',       de: 'Einrichten und reparieren', nl: 'Instellen en repareren', sv: 'Installera och fixa' } },
  { icon: '✂️', slug: 'diy-crafts',   en: 'DIY & Crafts',   de: 'Heimwerken',       nl: 'Knutselen',        sv: 'Gör det själv',   desc: { en: 'Create and make',    de: 'Basteln und schaffen', nl: 'Maken en creëren', sv: 'Skapa och göra' } },
]

const HERO = {
  en: { title: 'Step-by-step guides for everything', sub: 'Simple instructions that actually work' },
  de: { title: 'Schritt-für-Schritt Anleitungen für alles', sub: 'Einfache Anweisungen die wirklich funktionieren' },
  nl: { title: 'Stap voor stap handleidingen voor alles', sub: 'Eenvoudige instructies die echt werken' },
  sv: { title: 'Steg-för-steg guider för allt', sub: 'Enkla instruktioner som faktiskt fungerar' },
}

export default function HomePage({ params }) {
  const { lang } = params
  const h = HERO[lang] ?? HERO.en

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', padding: '0 16px' }}>
      {/* Hero */}
      <div style={{ padding: '32px 0 20px' }}>
        <h1 style={{ fontSize: 'clamp(22px, 4vw, 32px)', fontWeight: 500, marginBottom: '8px', lineHeight: 1.3 }}>
          {h.title}
        </h1>
        <p style={{ fontSize: '15px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          {h.sub}
        </p>
      </div>

      {/* Search bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        background: 'var(--search-bg)',
        border: '0.5px solid var(--border)',
        borderRadius: '24px',
        padding: '10px 18px',
        marginBottom: '28px',
        maxWidth: '480px',
      }}>
        <span>🔍</span>
        <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
          { lang === 'de' ? 'Anleitung suchen...' : lang === 'nl' ? 'Handleiding zoeken...' : lang === 'sv' ? 'Sök guide...' : 'Search for a guide...' }
        </span>
      </div>

      {/* Categories grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '12px',
        marginBottom: '32px',
      }}>
        {CATEGORIES.map(cat => (
          <Link key={cat.slug} href={`/${lang}/${cat.slug}`} style={{
            background: 'var(--card-bg)',
            border: '0.5px solid var(--border)',
            borderRadius: '12px',
            padding: '16px',
            display: 'block',
            transition: 'border-color 0.15s',
          }}>
            <div style={{ fontSize: '24px', marginBottom: '8px' }}>{cat.icon}</div>
            <div style={{ fontSize: '14px', fontWeight: 500, marginBottom: '4px' }}>{cat[lang] ?? cat.en}</div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{cat.desc[lang] ?? cat.desc.en}</div>
          </Link>
        ))}
      </div>
    </div>
  )
}