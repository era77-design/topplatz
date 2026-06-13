import fs from 'fs'
import path from 'path'
import matter from 'gray-matter'
import Link from 'next/link'

const LANGS = ['en', 'de', 'nl', 'sv']

const CATEGORIES = [
  { slug: 'home-garden',  icon: '🏠', en: 'Home & Garden',  de: 'Haus & Garten',    nl: 'Huis & Tuin',      sv: 'Hem & Trädgård' },
  { slug: 'kitchen-food', icon: '🍳', en: 'Kitchen & Food', de: 'Küche & Essen',    nl: 'Keuken & Eten',    sv: 'Kök & Mat' },
  { slug: 'tech-devices', icon: '💻', en: 'Tech & Devices', de: 'Technik & Geräte', nl: 'Tech & Apparaten', sv: 'Teknik & Enheter' },
  { slug: 'diy-crafts',   icon: '✂️', en: 'DIY & Crafts',   de: 'Heimwerken',       nl: 'Knutselen',        sv: 'Gör det själv' },
  { slug: 'general',      icon: '📖', en: 'General',        de: 'Allgemein',        nl: 'Algemeen',         sv: 'Allmänt' },
]

const UI = {
  en: { home: 'Home', contents: 'Contents', whatYouNeed: '🛒 What You Need', steps: '📋 Steps', tips: '💡 Tips & Tricks', warnings: '⚠️ Warnings', faq: '❓ Frequently Asked Questions', related: 'Related Guides', helpful: 'Was this guide helpful?', yes: 'Yes', no: 'Not really', share: 'Share', print: 'Print', readTime: 'min read', difficulty: 'Difficulty', jumpTo: 'Jump to steps ↓', adLabel: 'Advertisement' },
  de: { home: 'Startseite', contents: 'Inhalt', whatYouNeed: '🛒 Was Sie brauchen', steps: '📋 Schritte', tips: '💡 Tipps & Tricks', warnings: '⚠️ Warnungen', faq: '❓ Häufige Fragen', related: 'Ähnliche Anleitungen', helpful: 'War diese Anleitung hilfreich?', yes: 'Ja', no: 'Nicht wirklich', share: 'Teilen', print: 'Drucken', readTime: 'Min. Lesezeit', difficulty: 'Schwierigkeit', jumpTo: 'Zu den Schritten ↓', adLabel: 'Werbung' },
  nl: { home: 'Home', contents: 'Inhoud', whatYouNeed: '🛒 Wat u nodig heeft', steps: '📋 Stappen', tips: '💡 Tips & Tricks', warnings: '⚠️ Waarschuwingen', faq: '❓ Veelgestelde vragen', related: 'Gerelateerde handleidingen', helpful: 'Was deze handleiding nuttig?', yes: 'Ja', no: 'Niet echt', share: 'Delen', print: 'Afdrukken', readTime: 'min lezen', difficulty: 'Moeilijkheid', jumpTo: 'Naar stappen ↓', adLabel: 'Advertentie' },
  sv: { home: 'Hem', contents: 'Innehåll', whatYouNeed: '🛒 Vad du behöver', steps: '📋 Steg', tips: '💡 Tips & Tricks', warnings: '⚠️ Varningar', faq: '❓ Vanliga frågor', related: 'Relaterade guider', helpful: 'Var den här guiden till hjälp?', yes: 'Ja', no: 'Inte riktigt', share: 'Dela', print: 'Skriv ut', readTime: 'min läsning', difficulty: 'Svårighetsgrad', jumpTo: 'Till stegen ↓', adLabel: 'Annons' },
}

function detectCategory(keyword = '', slug = '') {
  const t = `${keyword} ${slug}`.toLowerCase()
  if (/clean|fix|repair|build|grow|garden|home|house|door|pipe|leak|wobbly|wood|paint|bed bug|pest|lawn|plant/.test(t)) return 'home-garden'
  if (/cook|recipe|food|kitchen|bake|meal|dish|ingredient|eat|drink|coffee|tea|sauce/.test(t)) return 'kitchen-food'
  if (/install|tech|computer|phone|wifi|software|app|delete|account|facebook|instagram|chrome|node|windows|mac|android|ios|internet/.test(t)) return 'tech-devices'
  if (/craft|diy|sew|knit|crochet|origami|candle|jewelry|decor/.test(t)) return 'diy-crafts'
  return 'general'
}

function getArticle(lang, slug) {
  const fp = path.join(process.cwd(), 'content', lang, `${slug}.mdx`)
  if (!fs.existsSync(fp)) return null
  const { data, content } = matter(fs.readFileSync(fp, 'utf-8'))
  return { fm: data, content }
}

function getRelated(lang, currentSlug, category, limit = 3) {
  const dir = path.join(process.cwd(), 'content', lang)
  if (!fs.existsSync(dir)) return []
  const files = fs.readdirSync(dir).filter(f => f.endsWith('.mdx') && f !== `${currentSlug}.mdx`).slice(0, 30)
  const same = [], other = []
  for (const file of files) {
    try {
      const { data } = matter(fs.readFileSync(path.join(dir, file), 'utf-8'))
      const slug = file.replace('.mdx', '')
      const cat = data.category || detectCategory(data.keyword, slug)
      const a = { slug, ...data, category: cat }
      cat === category ? same.push(a) : other.push(a)
    } catch {}
  }
  return [...same, ...other].slice(0, limit)
}

export async function generateStaticParams() {
  const params = []
  for (const lang of LANGS) {
    const dir = path.join(process.cwd(), 'content', lang)
    if (!fs.existsSync(dir)) continue
    for (const file of fs.readdirSync(dir).filter(f => f.endsWith('.mdx'))) {
      params.push({ lang, slug: file.replace('.mdx', '') })
    }
  }
  return params
}

export async function generateMetadata({ params }) {
  const { lang, slug } = await params
  const article = getArticle(lang, slug)
  if (!article) return {}
  const { fm } = article
  return {
    title: fm.title,
    description: fm.description,
    openGraph: { title: fm.title, description: fm.description, images: fm.photoUrl ? [{ url: fm.photoUrl }] : [] },
    alternates: { canonical: `https://topplatz.com/${lang}/${slug}` },
  }
}

// ── MARKDOWN HELPERS ──────────────────────────────────────────

function slug(text) {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/-$/, '')
}

function inline(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code style="background:var(--bg-secondary);padding:1px 5px;border-radius:4px;font-size:0.9em">$1</code>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" style="color:var(--text);text-decoration:underline">$1</a>')
}

function renderLines(lines) {
  const out = []
  let listBuf = []
  const flush = () => {
    if (!listBuf.length) return
    out.push(`<ul style="padding-left:20px;margin:0 0 14px">${listBuf.map(i => `<li style="margin-bottom:6px;line-height:1.75;color:var(--text-secondary)">${inline(i)}</li>`).join('')}</ul>`)
    listBuf = []
  }
  for (const line of lines) {
    const t = line.trim()
    if (!t) { flush(); continue }
    if (t.startsWith('- ')) { listBuf.push(t.slice(2)); continue }
    flush()
    if (t.startsWith('> ')) {
      out.push(`<div style="background:var(--bg-secondary);border-left:3px solid var(--border);border-radius:0 8px 8px 0;padding:10px 14px;margin:12px 0;font-size:14px;color:var(--text-secondary);font-style:italic">${inline(t.slice(2))}</div>`)
    } else {
      out.push(`<p style="margin:0 0 12px;line-height:1.8;color:var(--text-secondary);font-size:15px">${inline(t)}</p>`)
    }
  }
  flush()
  return out.join('')
}

// ── CONTENT PARSER ────────────────────────────────────────────

function parseContent(raw) {
  const clean = raw.replace(/!\[[^\]]*\]\([^)]+\)\n\*Photo by[\s\S]*?on \[Unsplash\][^\n]*/g, '').replace(/!\[[^\]]*\]\([^)]+\)/g, '').trim()
  const sections = []
  let cur = null
  let introLines = []
  for (const line of clean.split('\n')) {
    if (line.startsWith('## ')) {
      if (cur) sections.push(cur)
      else if (introLines.length) { sections.push({ type: 'intro', lines: introLines }); introLines = [] }
      const heading = line.slice(3).trim()
      cur = { type: 'section', heading, id: slug(heading), lines: [], subsections: [] }
    } else if (line.startsWith('### ') && cur) {
      const heading = line.slice(4).trim()
      cur.subsections.push({ heading, id: slug(heading), lines: [] })
    } else if (cur) {
      cur.subsections.length ? cur.subsections[cur.subsections.length - 1].lines.push(line) : cur.lines.push(line)
    } else {
      introLines.push(line)
    }
  }
  if (cur) sections.push(cur)
  else if (introLines.length) sections.push({ type: 'intro', lines: introLines })
  return sections
}

// ── AD SLOT ───────────────────────────────────────────────────

function AdSlot({ slot, label = 'Advertisement' }) {
  return (
    <div className={`ad-slot ad-slot-${slot}`} style={{ textAlign: 'center', padding: '8px 0', margin: '20px 0' }}>
      <p style={{ fontSize: '10px', color: 'var(--text-secondary)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</p>
      <ins className="adsbygoogle"
        style={{ display: 'block', minHeight: '90px', background: 'var(--bg-secondary)', borderRadius: '8px' }}
        data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"
        data-ad-slot={slot}
        data-ad-format="auto"
        data-full-width-responsive="true"
      />
    </div>
  )
}

// ── MAIN PAGE ─────────────────────────────────────────────────

export default async function ArticlePage({ params }) {
  const { lang, slug: articleSlug } = await params
  const article = getArticle(lang, articleSlug)
  const t = UI[lang] || UI.en

  if (!article) {
    return (
      <div style={{ maxWidth: '760px', margin: '0 auto', padding: '64px 16px', textAlign: 'center' }}>
        <h1 style={{ fontSize: '24px', marginBottom: '12px' }}>404</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Article not found</p>
        <Link href={`/${lang}`} style={{ color: 'var(--text)', textDecoration: 'underline' }}>{t.home}</Link>
      </div>
    )
  }

  const { fm, content } = article
  const category = fm.category || detectCategory(fm.keyword, articleSlug)
  const catInfo = CATEGORIES.find(c => c.slug === category) || CATEGORIES[4]
  const catName = catInfo[lang] || catInfo.en
  const sections = parseContent(content)
  const related = getRelated(lang, articleSlug, category)

  // TOC from sections
  const toc = sections.filter(s => s.type === 'section').map(s => ({
    text: s.heading, id: s.id,
    subs: (s.subsections || []).filter(sub => !/step \d+/i.test(sub.heading)).map(sub => ({ text: sub.heading, id: sub.id }))
  }))

  // Identify step subsections
  const stepSection = sections.find(s => s.type === 'section' && /^steps?$/i.test(s.heading))
  const steps = stepSection?.subsections || []

  // FAQ items
  const faqSection = sections.find(s => s.type === 'section' && /faq|frequently/i.test(s.heading))
  const faqs = []
  if (faqSection) {
    let q = null
    for (const line of faqSection.lines) {
      const t2 = line.trim()
      if (t2.startsWith('**') && t2.endsWith('**')) { q = t2.replace(/\*\*/g, '') }
      else if (q && t2) { faqs.push({ q, a: t2 }); q = null }
    }
  }

  // ── SCHEMA.ORG ──────────────────────────────────────────────

  const howToSchema = {
    '@context': 'https://schema.org',
    '@type': 'HowTo',
    name: fm.title,
    description: fm.description,
    totalTime: `PT${fm.timeMinutes || 15}M`,
    image: fm.photoUrl ? { '@type': 'ImageObject', url: fm.photoUrl } : undefined,
    supply: sections.find(s => s.type === 'section' && /what you need|was Sie brauchen|wat je nodig|vad du behöver/i.test(s.heading))?.lines
      .filter(l => l.trim().startsWith('- '))
      .map(l => ({ '@type': 'HowToSupply', name: l.trim().slice(2) })),
    step: steps.map((step, i) => ({
      '@type': 'HowToStep',
      position: i + 1,
      name: step.heading.replace(/^Step \d+:\s*/i, ''),
      text: step.lines.filter(l => l.trim() && !l.trim().startsWith('>')).join(' ').replace(/\*\*(.*?)\*\*/g, '$1'),
    })),
  }

  const breadcrumbSchema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: t.home, item: `https://topplatz.com/${lang}` },
      { '@type': 'ListItem', position: 2, name: catName, item: `https://topplatz.com/${lang}/category/${category}` },
      { '@type': 'ListItem', position: 3, name: fm.title, item: `https://topplatz.com/${lang}/${articleSlug}` },
    ],
  }

  const faqSchema = faqs.length > 0 ? {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faqs.map(f => ({
      '@type': 'Question',
      name: f.q,
      acceptedAnswer: { '@type': 'Answer', text: f.a },
    })),
  } : null

  // ── RENDER ──────────────────────────────────────────────────

  return (
    <div style={{ maxWidth: '1060px', margin: '0 auto', padding: '0 16px 48px' }}>

      {/* Schema.org */}
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(howToSchema) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }} />
      {faqSchema && <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }} />}

      {/* Breadcrumbs */}
      <nav aria-label="breadcrumb" style={{ padding: '16px 0 0', fontSize: '13px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
        <Link href={`/${lang}`} style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>{t.home}</Link>
        <span>›</span>
        <Link href={`/${lang}/category/${category}`} style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>{catName}</Link>
        <span>›</span>
        <span style={{ color: 'var(--text)', maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{fm.title}</span>
      </nav>

      {/* Hero photo */}
      {fm.photoUrl && (
        <div style={{ margin: '16px 0' }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={fm.photoUrl} alt={fm.photoAlt || fm.title} style={{ width: '100%', maxHeight: '420px', objectFit: 'cover', borderRadius: '14px', display: 'block' }} />
          {fm.photoAuthor && (
            <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '5px' }}>
              Photo by <a href={fm.photoUnsplash} target="_blank" rel="noopener" style={{ color: 'var(--text-secondary)' }}>{fm.photoAuthor}</a> on Unsplash
            </p>
          )}
        </div>
      )}

      {/* Title area */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' }}>
          <Link href={`/${lang}/category/${category}`} style={{ textDecoration: 'none' }}>
            <span style={{ fontSize: '12px', background: 'var(--bg-secondary)', border: '0.5px solid var(--border)', padding: '4px 12px', borderRadius: '20px', color: 'var(--text-secondary)' }}>
              {catInfo.icon} {catName}
            </span>
          </Link>
          {fm.timeMinutes && <span style={{ fontSize: '12px', background: 'var(--bg-secondary)', border: '0.5px solid var(--border)', padding: '4px 12px', borderRadius: '20px', color: 'var(--text-secondary)' }}>⏱ {fm.timeMinutes} {t.readTime}</span>}
          {fm.difficulty && <span style={{ fontSize: '12px', background: 'var(--bg-secondary)', border: '0.5px solid var(--border)', padding: '4px 12px', borderRadius: '20px', color: 'var(--text-secondary)' }}>📊 {fm.difficulty}</span>}
        </div>
        <h1 style={{ fontSize: 'clamp(22px, 4vw, 34px)', fontWeight: 500, lineHeight: 1.25, marginBottom: '12px', color: 'var(--text)' }}>{fm.title}</h1>
        <p style={{ fontSize: '16px', color: 'var(--text-secondary)', lineHeight: 1.7 }}>{fm.description}</p>
      </div>

      {/* At a Glance + Jump to steps */}
      <div style={{ background: 'var(--bg-secondary)', border: '0.5px solid var(--border)', borderRadius: '12px', padding: '16px 20px', marginBottom: '20px', display: 'flex', gap: '16px', alignItems: 'flex-start', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: '200px' }}>
          <p style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Quick Summary</p>
          {sections.find(s => s.type === 'intro') && (
            <p style={{ fontSize: '14px', color: 'var(--text)', lineHeight: 1.65, margin: 0 }}>
              {sections.find(s => s.type === 'intro').lines.find(l => l.trim())?.trim() || fm.description}
            </p>
          )}
        </div>
        {steps.length > 0 && (
          <a href="#steps" style={{ display: 'inline-block', background: 'var(--text)', color: 'var(--bg)', padding: '10px 20px', borderRadius: '8px', fontSize: '14px', fontWeight: 500, textDecoration: 'none', whiteSpace: 'nowrap', flexShrink: 0 }}>
            {t.jumpTo}
          </a>
        )}
      </div>

      {/* AD #1 — after intro */}
      <AdSlot slot="1234567890" label={t.adLabel} />

      {/* Desktop layout: content + sidebar */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 280px', gap: '32px', alignItems: 'start' }} className="article-layout">

        {/* Main content */}
        <main>

          {/* TOC — mobile (shown inline) */}
          {toc.length > 2 && (
            <div style={{ background: 'var(--bg-secondary)', border: '0.5px solid var(--border)', borderRadius: '12px', padding: '16px', marginBottom: '28px' }} className="toc-mobile">
              <p style={{ fontSize: '13px', fontWeight: 500, marginBottom: '10px', color: 'var(--text)' }}>📋 {t.contents}</p>
              <ol style={{ paddingLeft: '18px', margin: 0 }}>
                {toc.map((item, i) => (
                  <li key={i} style={{ marginBottom: '6px' }}>
                    <a href={`#${item.id}`} style={{ fontSize: '13px', color: 'var(--text-secondary)', textDecoration: 'none' }}>{item.text}</a>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Sections */}
          {sections.map((section, si) => {
            if (section.type === 'intro') return null
            const isSteps    = /^steps?$/i.test(section.heading)
            const isNeed     = /what you need|was Sie brauchen|wat je nodig|vad du behöver/i.test(section.heading)
            const isTips     = /tips?|tricks?/i.test(section.heading)
            const isWarnings = /warning|warnung|waarschuwing|varning/i.test(section.heading)
            const isFaq      = /faq|frequently|häufig|veelgesteld|vanliga/i.test(section.heading)
            const sectionLabel = isSteps ? t.steps : isNeed ? t.whatYouNeed : isTips ? t.tips : isWarnings ? t.warnings : isFaq ? t.faq : section.heading

            return (
              <section key={si} id={section.id} style={{ marginBottom: '32px' }}>
                <h2 style={{ fontSize: '19px', fontWeight: 500, marginBottom: '16px', paddingBottom: '10px', borderBottom: '0.5px solid var(--border)', color: 'var(--text)' }}>
                  {sectionLabel}
                </h2>

                {/* Inline section content */}
                {section.lines.length > 0 && !isFaq && (
                  <div dangerouslySetInnerHTML={{ __html: renderLines(section.lines) }} />
                )}

                {/* Step cards */}
                {isSteps && steps.map((step, i) => (
                  <div key={i} id={step.id} style={{ border: '0.5px solid var(--border)', borderRadius: '12px', padding: '16px 18px', marginBottom: '12px', background: 'var(--card-bg)' }}>
                    <div style={{ display: 'flex', gap: '14px', alignItems: 'flex-start' }}>
                      <div style={{ minWidth: '32px', height: '32px', borderRadius: '50%', background: 'var(--text)', color: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px', fontWeight: 500, flexShrink: 0 }}>
                        {i + 1}
                      </div>
                      <div style={{ flex: 1 }}>
                        <h3 style={{ fontSize: '15px', fontWeight: 500, marginBottom: '8px', color: 'var(--text)', lineHeight: 1.4 }}>
                          {step.heading.replace(/^Step \d+:\s*/i, '')}
                        </h3>
                        <div dangerouslySetInnerHTML={{ __html: renderLines(step.lines) }} />
                      </div>
                    </div>
                    {/* AD #2 after step 3 */}
                    {i === 2 && <AdSlot slot="0987654321" label={t.adLabel} />}
                  </div>
                ))}

                {/* Tips styled */}
                {isTips && (
                  <div style={{ background: 'rgba(255, 248, 220, 0.6)', border: '0.5px solid #e6c97a', borderRadius: '12px', padding: '16px 18px' }}>
                    <div dangerouslySetInnerHTML={{ __html: renderLines(section.lines) }} />
                  </div>
                )}

                {/* Warnings styled */}
                {isWarnings && (
                  <div style={{ background: 'rgba(255, 235, 205, 0.6)', border: '0.5px solid #e69a4a', borderRadius: '12px', padding: '16px 18px' }}>
                    <div dangerouslySetInnerHTML={{ __html: renderLines(section.lines) }} />
                  </div>
                )}

                {/* FAQ */}
                {isFaq && (
                  <div>
                    {faqs.map((faq, fi) => (
                      <div key={fi} style={{ borderBottom: '0.5px solid var(--border)', padding: '16px 0' }}>
                        <h3 style={{ fontSize: '15px', fontWeight: 500, color: 'var(--text)', marginBottom: '8px', lineHeight: 1.4 }}>{faq.q}</h3>
                        <p style={{ fontSize: '14px', color: 'var(--text-secondary)', lineHeight: 1.75, margin: 0 }}>{faq.a}</p>
                      </div>
                    ))}
                  </div>
                )}

                {/* AD #3 after Tips */}
                {isTips && <AdSlot slot="1122334455" label={t.adLabel} />}
              </section>
            )
          })}

          {/* AD #4 — end of article */}
          <AdSlot slot="5544332211" label={t.adLabel} />

          {/* Was this helpful + Share */}
          <div style={{ border: '0.5px solid var(--border)', borderRadius: '12px', padding: '20px', textAlign: 'center', marginBottom: '32px' }}>
            <p style={{ fontSize: '15px', fontWeight: 500, marginBottom: '14px', color: 'var(--text)' }}>{t.helpful}</p>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginBottom: '16px' }}>
              <button style={{ padding: '8px 24px', borderRadius: '8px', border: '0.5px solid var(--border)', background: 'var(--bg-secondary)', color: 'var(--text)', fontSize: '14px', cursor: 'pointer' }}>
                👍 {t.yes}
              </button>
              <button style={{ padding: '8px 24px', borderRadius: '8px', border: '0.5px solid var(--border)', background: 'var(--bg-secondary)', color: 'var(--text-secondary)', fontSize: '14px', cursor: 'pointer' }}>
                👎 {t.no}
              </button>
            </div>
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-secondary)', marginRight: '4px' }}>{t.share}:</span>
              {[['Facebook', 'f', `https://www.facebook.com/sharer/sharer.php?u=https://topplatz.com/${lang}/${articleSlug}`],
                ['Twitter', 'X', `https://twitter.com/intent/tweet?url=https://topplatz.com/${lang}/${articleSlug}&text=${encodeURIComponent(fm.title)}`],
                ['Print', '🖨', 'javascript:window.print()']].map(([name, icon, href]) => (
                <a key={name} href={href} target={name !== 'Print' ? '_blank' : undefined} rel="noopener" aria-label={name}
                  style={{ padding: '6px 14px', borderRadius: '6px', border: '0.5px solid var(--border)', background: 'var(--bg-secondary)', color: 'var(--text-secondary)', fontSize: '13px', textDecoration: 'none', display: 'inline-block' }}>
                  {icon}
                </a>
              ))}
            </div>
          </div>
        </main>

        {/* Sidebar — desktop */}
        <aside className="article-sidebar" style={{ position: 'sticky', top: '80px' }}>

          {/* TOC desktop */}
          {toc.length > 1 && (
            <div style={{ background: 'var(--bg-secondary)', border: '0.5px solid var(--border)', borderRadius: '12px', padding: '16px', marginBottom: '16px' }}>
              <p style={{ fontSize: '13px', fontWeight: 500, marginBottom: '12px', color: 'var(--text)' }}>📋 {t.contents}</p>
              <nav>
                {toc.map((item, i) => (
                  <div key={i} style={{ marginBottom: '2px' }}>
                    <a href={`#${item.id}`} style={{ display: 'block', padding: '5px 8px', fontSize: '13px', color: 'var(--text-secondary)', textDecoration: 'none', borderRadius: '6px', lineHeight: 1.4 }}>
                      {item.text}
                    </a>
                    {item.subs?.map((sub, j) => (
                      <a key={j} href={`#${sub.id}`} style={{ display: 'block', padding: '3px 8px 3px 20px', fontSize: '12px', color: 'var(--text-secondary)', textDecoration: 'none', borderRadius: '6px', opacity: 0.8 }}>
                        {sub.text}
                      </a>
                    ))}
                  </div>
                ))}
              </nav>
            </div>
          )}

          {/* Sidebar AD 300x600 */}
          <div style={{ textAlign: 'center' }}>
            <p style={{ fontSize: '10px', color: 'var(--text-secondary)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{t.adLabel}</p>
            <ins className="adsbygoogle"
              style={{ display: 'block', minHeight: '250px', background: 'var(--bg-secondary)', borderRadius: '8px' }}
              data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"
              data-ad-slot="6677889900"
              data-ad-format="vertical"
            />
          </div>
        </aside>
      </div>

      {/* Related Articles */}
      {related.length > 0 && (
        <section style={{ marginTop: '16px', paddingTop: '28px', borderTop: '0.5px solid var(--border)' }}>
          <h2 style={{ fontSize: '18px', fontWeight: 500, marginBottom: '16px', color: 'var(--text)' }}>{t.related}</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '14px' }}>
            {related.map(rel => (
              <Link key={rel.slug} href={`/${lang}/${rel.slug}`} style={{ textDecoration: 'none', display: 'block' }}>
                <div style={{ border: '0.5px solid var(--border)', borderRadius: '12px', overflow: 'hidden', background: 'var(--card-bg)' }}>
                  {rel.photoUrl && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={rel.photoUrl} alt={rel.photoAlt || rel.title} style={{ width: '100%', height: '130px', objectFit: 'cover', display: 'block' }} />
                  )}
                  <div style={{ padding: '12px' }}>
                    <p style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text)', lineHeight: 1.4, margin: 0 }}>{rel.title}</p>
                    {rel.timeMinutes && <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>⏱ {rel.timeMinutes} min</p>}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Responsive styles */}
      <style>{`
        @media (max-width: 768px) {
          .article-layout { grid-template-columns: 1fr !important; }
          .article-sidebar { display: none !important; }
          .toc-mobile { display: block !important; }
        }
        @media (min-width: 769px) {
          .toc-mobile { display: none !important; }
          .article-sidebar { display: block !important; }
        }
        @media print {
          .ad-slot, .article-sidebar, nav[aria-label="breadcrumb"] { display: none !important; }
        }
      `}</style>
    </div>
  )
}
