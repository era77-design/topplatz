import fs from 'fs'
import path from 'path'
import matter from 'gray-matter'

export const CATEGORIES = [
  { slug: 'home-garden',  icon: '🏠', en: 'Home & Garden',  de: 'Haus & Garten',    nl: 'Huis & Tuin',      sv: 'Hem & Trädgård' },
  { slug: 'kitchen-food', icon: '🍳', en: 'Kitchen & Food', de: 'Küche & Essen',    nl: 'Keuken & Eten',    sv: 'Kök & Mat' },
  { slug: 'tech-devices', icon: '💻', en: 'Tech & Devices', de: 'Technik & Geräte', nl: 'Tech & Apparaten', sv: 'Teknik & Enheter' },
  { slug: 'diy-crafts',   icon: '✂️', en: 'DIY & Crafts',   de: 'Heimwerken',       nl: 'Knutselen',        sv: 'Gör det själv' },
  { slug: 'general',      icon: '📖', en: 'General',        de: 'Allgemein',        nl: 'Algemeen',         sv: 'Allmänt' },
]

// Авто-определение категории по ключевику и slug
export function detectCategory(keyword = '', slug = '') {
  const text = `${keyword} ${slug}`.toLowerCase()
  if (/clean|fix|repair|build|grow|garden|home|house|door|pipe|leak|wobbly|wood|paint|bed bug|pest|weed|lawn|plant/.test(text)) return 'home-garden'
  if (/cook|recipe|food|kitchen|bake|meal|dish|ingredient|eat|drink|coffee|tea|sauce/.test(text)) return 'kitchen-food'
  if (/install|tech|computer|phone|wifi|software|app|delete|account|facebook|instagram|chrome|node|windows|mac|android|ios|internet/.test(text)) return 'tech-devices'
  if (/craft|diy|sew|knit|crochet|origami|candle|jewelry|decor/.test(text)) return 'diy-crafts'
  return 'general'
}

// Получить все статьи для языка
export function getArticles(lang) {
  const contentDir = path.join(process.cwd(), 'content', lang)
  if (!fs.existsSync(contentDir)) return []

  const files = fs.readdirSync(contentDir).filter(f => f.endsWith('.mdx'))

  return files.map(file => {
    const slug = file.replace('.mdx', '')
    try {
      const { data } = matter(fs.readFileSync(path.join(contentDir, file), 'utf-8'))
      const category = data.category || detectCategory(data.keyword, slug)
      return { slug, lang, category, ...data }
    } catch {
      return { slug, lang, category: 'general', title: slug, description: '' }
    }
  }).sort((a, b) => new Date(b.createdAt || 0) - new Date(a.createdAt || 0))
}

// Получить статьи по категории
export function getArticlesByCategory(lang, categorySlug) {
  return getArticles(lang).filter(a => a.category === categorySlug)
}

// Получить категорию по slug
export function getCategoryInfo(slug) {
  return CATEGORIES.find(c => c.slug === slug) || CATEGORIES[CATEGORIES.length - 1]
}

// Получить название категории на языке
export function getCategoryName(slug, lang) {
  const cat = getCategoryInfo(slug)
  return cat[lang] || cat.en
}
