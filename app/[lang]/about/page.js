export const runtime = 'edge'

export default function AboutPage({ params }) {
  const { lang } = params

  const content = {
    en: {
      title: 'About TopPlatz',
      body: 'TopPlatz is a collection of practical how-to guides covering everyday topics — from home repair and cooking to gardening and technology. Our goal is to provide clear, step-by-step instructions that actually work.',
      mission: 'Our Mission',
      missionText: 'We believe everyone deserves access to clear, practical information. Every guide on TopPlatz is written to be easy to follow, with real steps and honest tips.',
    },
    de: {
      title: 'Über TopPlatz',
      body: 'TopPlatz ist eine Sammlung praktischer Anleitungen zu alltäglichen Themen — von Heimwerken und Kochen bis hin zu Gartenarbeit und Technologie.',
      mission: 'Unsere Mission',
      missionText: 'Wir glauben, dass jeder Zugang zu klaren, praktischen Informationen verdient. Jede Anleitung auf TopPlatz ist einfach zu befolgen.',
    },
    nl: {
      title: 'Over TopPlatz',
      body: 'TopPlatz is een verzameling praktische handleidingen over alledaagse onderwerpen — van thuisreparaties en koken tot tuinieren en technologie.',
      mission: 'Onze missie',
      missionText: 'We geloven dat iedereen toegang verdient tot duidelijke, praktische informatie. Elke handleiding op TopPlatz is gemakkelijk te volgen.',
    },
    sv: {
      title: 'Om TopPlatz',
      body: 'TopPlatz är en samling praktiska guider om vardagliga ämnen — från hemreparationer och matlagning till trädgårdsarbete och teknik.',
      mission: 'Vårt uppdrag',
      missionText: 'Vi tror att alla förtjänar tillgång till tydlig, praktisk information. Varje guide på TopPlatz är lätt att följa.',
    }
  }

  const t = content[lang] ?? content.en

  return (
    <main className="max-w-3xl mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold mb-6">{t.title}</h1>
      <p className="text-gray-700 mb-8 text-lg">{t.body}</p>
      <h2 className="text-xl font-semibold mb-2">{t.mission}</h2>
      <p className="text-gray-700">{t.missionText}</p>
    </main>
  )
}