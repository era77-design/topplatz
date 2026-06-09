export const runtime = 'edge'

export default function HomePage({ params }) {
  const { lang } = params

  const content = {
    en: { title: 'How-To Guides', subtitle: 'Step by step instructions for everything' },
    de: { title: 'Anleitungen',   subtitle: 'Schritt-für-Schritt Anleitungen für alles' },
    nl: { title: 'Handleidingen', subtitle: 'Stap voor stap instructies voor alles' },
    sv: { title: 'Guider',        subtitle: 'Steg-för-steg instruktioner för allt' },
  }

  const t = content[lang] ?? content.en

  return (
    <main className="max-w-4xl mx-auto px-4 py-12">
      <h1 className="text-4xl font-bold mb-4">{t.title}</h1>
      <p className="text-xl text-gray-600">{t.subtitle}</p>
    </main>
  )
}