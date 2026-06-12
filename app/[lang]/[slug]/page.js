import fs from 'fs'
import path from 'path'
import matter from 'gray-matter'

const LANGS = ['en', 'de', 'nl', 'sv']

// Читаем статью из MDX файла
function getArticle(lang, slug) {
  const filepath = path.join(process.cwd(), 'content', lang, `${slug}.mdx`)
  if (!fs.existsSync(filepath)) return null
  const raw = fs.readFileSync(filepath, 'utf-8')
  const { data, content } = matter(raw)
  return { frontmatter: data, content }
}

// Генерируем статические пути для всех статей
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

// SEO мета-теги
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

// Простой Markdown → HTML конвертер
function parseMarkdown(md) {
  return md
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^> (.+)/gim, '<blockquote>$1</blockquote>')
    .replace(/^- (.+)/gim, '<li>$1</li>')
    .replace(/(<li>[\s\S]*?<\/li>)/g, '<ul>$1</ul>')
    .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" />')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    .replace(/\n\n+/g, '</p><p>')
    .replace(/^(?!<[hublipa])/gim, '')
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

  return (
    <div style={{ maxWidth: '760px', margin: '0 auto', padding: '32px 16px' }}>

      {/* Фото */}
      {fm.photoUrl && (
        <div style={{ marginBottom: '28px' }}>
          <img
            src={fm.photoUrl}
            alt={fm.photoAlt || fm.title}
            style={{
              width: '100%',
              borderRadius: '12px',
              maxHeight: '420px',
              objectFit: 'cover',
              display: 'block',
            }}
          />
          {fm.photoAuthor && (
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '6px' }}>
              Photo by{' '}
              <a href={fm.photoUnsplash} target="_blank" rel="noopener"
                style={{ color: 'var(--text-secondary)' }}>
                {fm.photoAuthor}
              </a>{' '}
              on Unsplash
            </p>
          )}
        </div>
      )}

      {/* Бейджи */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
        {fm.timeMinutes && (
          <span style={{
            fontSize: '12px',
            background: 'var(--bg-secondary)',
            border: '0.5px solid var(--border)',
            padding: '4px 12px',
            borderRadius: '20px',
            color: 'var(--text-secondary)',
          }}>
            ⏱ {fm.timeMinutes} min
          </span>
        )}
        {fm.difficulty && (
          <span style={{
            fontSize: '12px',
            background: 'var(--bg-secondary)',
            border: '0.5px solid var(--border)',
            padding: '4px 12px',
            borderRadius: '20px',
            color: 'var(--text-secondary)',
          }}>
            📊 {fm.difficulty}
          </span>
        )}
      </div>

      {/* Заголовок */}
      <h1 style={{
        fontSize: 'clamp(22px, 4vw, 32px)',
        fontWeight: 500,
        lineHeight: 1.3,
        marginBottom: '16px',
        color: 'var(--text)',
      }}>
        {fm.title}
      </h1>

      <p style={{
        fontSize: '16px',
        color: 'var(--text-secondary)',
        lineHeight: 1.7,
        marginBottom: '32px',
        paddingBottom: '24px',
        borderBottom: '0.5px solid var(--border)',
      }}>
        {fm.description}
      </p>

      {/* Контент статьи */}
      <div
        className="article-body"
        dangerouslySetInnerHTML={{ __html: `<p>${parseMarkdown(content)}</p>` }}
      />

      {/* Стили статьи */}
      <style>{`
        .article-body h2 {
          font-size: 20px;
          font-weight: 500;
          margin: 36px 0 12px;
          color: var(--text);
          padding-top: 8px;
          border-top: 0.5px solid var(--border);
        }
        .article-body h3 {
          font-size: 17px;
          font-weight: 500;
          margin: 24px 0 8px;
          color: var(--text);
        }
        .article-body p {
          line-height: 1.8;
          margin-bottom: 14px;
          color: var(--text-secondary);
        }
        .article-body ul {
          padding-left: 20px;
          margin-bottom: 16px;
        }
        .article-body li {
          line-height: 1.8;
          margin-bottom: 6px;
          color: var(--text-secondary);
        }
        .article-body blockquote {
          border-left: 3px solid var(--border);
          padding: 10px 16px;
          margin: 16px 0;
          color: var(--text-secondary);
          background: var(--bg-secondary);
          border-radius: 0 8px 8px 0;
          font-style: italic;
        }
        .article-body strong {
          color: var(--text);
          font-weight: 500;
        }
        .article-body a {
          color: var(--text);
          text-decoration: underline;
          text-underline-offset: 3px;
        }
        .article-body img {
          width: 100%;
          border-radius: 12px;
          margin: 20px 0;
        }
        .article-body em {
          font-style: italic;
        }
      `}</style>
    </div>
  )
}
