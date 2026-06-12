import fs from 'fs'
import path from 'path'
import matter from 'gray-matter'

const LANGS = ['en', 'de', 'nl', 'sv']

function getArticle(lang, slug) {
  const filepath = path.join(process.cwd(), 'content', lang, `${slug}.mdx`)
  if (!fs.existsSync(filepath)) return null
  const { data, content } = matter(fs.readFileSync(filepath, 'utf-8'))
  return { frontmatter: data, content }
}

export async function generateStaticParams() {
  const params = []
  for (const lang of LANGS) {
    const contentDir = path.join(process.cwd(), 'content', lang)
    if (!fs.existsSync(contentDir)) continue
    const files = fs.readdirSync(contentDir).filter(f => f.endsWith('.mdx'))
    for (const file of files) {
      params.push({ lang, slug: file.replace('.mdx', '') })
    }
  }
  return params
}

export async function generateMetadata({ params }) {
  const { lang, slug } = await params
  const article = getArticle(lang, slug)
  if (!article) return {}
  const fm = article.frontmatter
  return {
    title: fm.title,
    description: fm.description,
    openGraph: {
      title: fm.title,
      description: fm.description,
      images: fm.photoUrl ? [{ url: fm.photoUrl }] : [],
    },
  }
}

// Парсим секции из MDX контента
function parseSections(content) {
  const sections = []
  const lines = content.split('\n')
  let current = { type: 'text', heading: null, lines: [] }

  for (const line of lines) {
    // Пропускаем фото из Unsplash
    if (line.startsWith('![') || line.startsWith('*Photo by')) continue

    if (line.startsWith('## ')) {
      if (current.lines.length > 0) sections.push(current)
      current = { type: 'section', heading: line.replace('## ', '').trim(), lines: [] }
    } else if (line.startsWith('### ')) {
      if (current.lines.length > 0) {
        sections.push(current)
        current = { type: 'subsection', heading: line.replace('### ', '').trim(), lines: [], parent: current.heading }
      } else {
        current = { type: 'subsection', heading: line.replace('### ', '').trim(), lines: [] }
      }
    } else {
      current.lines.push(line)
    }
  }
  if (current.lines.length > 0 || current.heading) sections.push(current)
  return sections
}

function renderLine(line) {
  return line
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    .replace(/^> (.+)/, '<span class="tip-line">💡 $1</span>')
}

function renderLines(lines) {
  const result = []
  let inList = false
  let listItems = []

  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed) {
      if (inList) {
        result.push(`<ul class="art-list">${listItems.map(i => `<li>${renderLine(i)}</li>`).join('')}</ul>`)
        listItems = []
        inList = false
      }
      continue
    }
    if (trimmed.startsWith('- ')) {
      inList = true
      listItems.push(trimmed.slice(2))
    } else if (trimmed.startsWith('> ')) {
      if (inList) {
        result.push(`<ul class="art-list">${listItems.map(i => `<li>${renderLine(i)}</li>`).join('')}</ul>`)
        listItems = []
        inList = false
      }
      result.push(`<div class="art-tip">${renderLine(trimmed)}</div>`)
    } else if (trimmed.startsWith('**') && trimmed.endsWith('**') && trimmed.split('**').length === 3) {
      result.push(`<p class="art-bold">${renderLine(trimmed)}</p>`)
    } else {
      if (inList) {
        result.push(`<ul class="art-list">${listItems.map(i => `<li>${renderLine(i)}</li>`).join('')}</ul>`)
        listItems = []
        inList = false
      }
      result.push(`<p class="art-p">${renderLine(trimmed)}</p>`)
    }
  }
  if (inList) {
    result.push(`<ul class="art-list">${listItems.map(i => `<li>${renderLine(i)}</li>`).join('')}</ul>`)
  }
  return result.join('')
}

export default async function ArticlePage({ params }) {
  const { lang, slug } = await params
  const article = getArticle(lang, slug)

  if (!article) {
    return (
      <div style={{ maxWidth: '760px', margin: '0 auto', padding: '64px 16px', textAlign: 'center' }}>
        <h1 style={{ fontSize: '24px', marginBottom: '12px' }}>404</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Article not found</p>
      </div>
    )
  }

  const { frontmatter: fm, content } = article
  const sections = parseSections(content)

  // Определяем шаги
  const stepSections = sections.filter(s => s.type === 'subsection' && /step \d+/i.test(s.heading))
  const otherSections = sections.filter(s => !(s.type === 'subsection' && /step \d+/i.test(s.heading)))

  return (
    <div style={{ maxWidth: '760px', margin: '0 auto', padding: '24px 16px 48px' }}>

      {/* Фото */}
      {fm.photoUrl && (
        <div style={{ marginBottom: '24px' }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={fm.photoUrl}
            alt={fm.photoAlt || fm.title}
            style={{ width: '100%', borderRadius: '12px', maxHeight: '380px', objectFit: 'cover', display: 'block' }}
          />
          {fm.photoAuthor && (
            <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '5px' }}>
              Photo by <a href={fm.photoUnsplash} target="_blank" rel="noopener" style={{ color: 'var(--text-secondary)' }}>{fm.photoAuthor}</a> on Unsplash
            </p>
          )}
        </div>
      )}

      {/* Бейджи */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '14px', flexWrap: 'wrap' }}>
        {fm.timeMinutes && (
          <span className="badge">⏱ {fm.timeMinutes} min</span>
        )}
        {fm.difficulty && (
          <span className="badge">📊 {fm.difficulty}</span>
        )}
      </div>

      {/* Заголовок */}
      <h1 style={{ fontSize: 'clamp(20px, 4vw, 30px)', fontWeight: 500, lineHeight: 1.3, marginBottom: '12px', color: 'var(--text)' }}>
        {fm.title}
      </h1>

      <p style={{ fontSize: '15px', color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: '28px', paddingBottom: '24px', borderBottom: '0.5px solid var(--border)' }}>
        {fm.description}
      </p>

      {/* Секции */}
      {otherSections.map((section, i) => {
        const isSteps = section.heading === 'Steps'
        const isWhatYouNeed = /what you need|was Sie brauchen|wat je nodig/i.test(section.heading || '')
        const isFaq = /faq|frequently/i.test(section.heading || '')
        const isTips = /tips|tricks/i.test(section.heading || '')
        const isWarnings = /warning/i.test(section.heading || '')

        return (
          <div key={i} style={{ marginBottom: '32px' }}>
            {section.heading && (
              <h2 style={{
                fontSize: '18px', fontWeight: 500, marginBottom: '16px',
                color: 'var(--text)', paddingBottom: '8px',
                borderBottom: '0.5px solid var(--border)',
              }}>
                {isSteps ? '📋 ' : isWhatYouNeed ? '🛒 ' : isFaq ? '❓ ' : isTips ? '💡 ' : isWarnings ? '⚠️ ' : ''}{section.heading}
              </h2>
            )}

            {/* Шаги внутри Steps секции */}
            {isSteps && stepSections.map((step, si) => (
              <div key={si} style={{
                background: 'var(--bg-secondary)',
                border: '0.5px solid var(--border)',
                borderRadius: '12px',
                padding: '16px 20px',
                marginBottom: '12px',
              }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                  <span style={{
                    minWidth: '28px', height: '28px', borderRadius: '50%',
                    background: 'var(--text)', color: 'var(--bg)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '13px', fontWeight: 500, flexShrink: 0, marginTop: '1px',
                  }}>
                    {si + 1}
                  </span>
                  <div style={{ flex: 1 }}>
                    <h3 style={{ fontSize: '15px', fontWeight: 500, marginBottom: '8px', color: 'var(--text)' }}>
                      {step.heading.replace(/^Step \d+:\s*/i, '')}
                    </h3>
                    <div dangerouslySetInnerHTML={{ __html: renderLines(step.lines) }} />
                  </div>
                </div>
              </div>
            ))}

            {/* FAQ */}
            {isFaq && (
              <div>
                {(() => {
                  const faqs = []
                  let q = null
                  for (const line of section.lines) {
                    const trimmed = line.trim()
                    if (trimmed.startsWith('**') && trimmed.endsWith('**')) {
                      q = trimmed.replace(/\*\*/g, '')
                    } else if (q && trimmed) {
                      faqs.push({ q, a: trimmed })
                      q = null
                    }
                  }
                  return faqs.map((faq, fi) => (
                    <div key={fi} style={{
                      borderBottom: '0.5px solid var(--border)',
                      padding: '14px 0',
                    }}>
                      <p style={{ fontWeight: 500, fontSize: '14px', color: 'var(--text)', marginBottom: '6px' }}>{faq.q}</p>
                      <p style={{ fontSize: '14px', color: 'var(--text-secondary)', lineHeight: 1.7 }}>{faq.a}</p>
                    </div>
                  ))
                })()}
              </div>
            )}

            {/* Обычный контент */}
            {!isSteps && !isFaq && (
              <div dangerouslySetInnerHTML={{ __html: renderLines(section.lines) }} />
            )}
          </div>
        )
      })}

      <style>{`
        .badge {
          font-size: 12px;
          background: var(--bg-secondary);
          border: 0.5px solid var(--border);
          padding: 4px 12px;
          border-radius: 20px;
          color: var(--text-secondary);
        }
        .art-p {
          line-height: 1.8;
          margin-bottom: 12px;
          color: var(--text-secondary);
          font-size: 15px;
        }
        .art-bold {
          line-height: 1.8;
          margin-bottom: 10px;
          color: var(--text);
          font-size: 15px;
          font-weight: 500;
        }
        .art-list {
          padding-left: 20px;
          margin-bottom: 14px;
        }
        .art-list li {
          line-height: 1.8;
          margin-bottom: 5px;
          color: var(--text-secondary);
          font-size: 15px;
        }
        .art-tip {
          background: var(--bg-secondary);
          border-left: 3px solid var(--border);
          padding: 10px 14px;
          margin: 12px 0;
          border-radius: 0 8px 8px 0;
          font-size: 14px;
          color: var(--text-secondary);
          font-style: italic;
        }
        .tip-line { display: block; }
        a { color: var(--text); text-decoration: underline; text-underline-offset: 3px; }
      `}</style>
    </div>
  )
}