export const runtime = 'edge'

export async function generateMetadata({ params }) {
  const { lang } = await params
  const titles = {
    en: 'About — TopPlatz',
    de: 'Über uns — TopPlatz',
    nl: 'Over ons — TopPlatz',
    sv: 'Om oss — TopPlatz',
  }
  return { title: titles[lang] || titles.en }
}

export default async function AboutPage({ params }) {
  const { lang } = await params

  const content = {
    en: { title: 'About TopPlatz', body: 'TopPlatz is a collection of practical how-to guides covering everyday topics — from home repair and cooking to gardening and technology.', mission: 'Our Mission', missionText: 'We believe everyone deserves access to clear, practical information. Every guide is written to be easy to follow, with real steps and honest tips.' },
    de: { title: 'Über TopPlatz', body: 'TopPlatz ist eine Sammlung praktischer Anleitungen zu alltäglichen Themen — von Heimwerken und Kochen bis hin zu Gartenarbeit und Technologie.', mission: 'Unsere Mission', missionText: 'Wir glauben, dass jeder Zugang zu klaren, praktischen Informationen verdient.' },
    nl: { title: 'Over TopPlatz', body: 'TopPlatz is een verzameling praktische handleidingen over alledaagse onderwerpen.', mission: 'Onze missie', missionText: 'We geloven dat iedereen toegang verdient tot duidelijke, praktische informatie.' },
    sv: { title: 'Om TopPlatz', body: 'TopPlatz är en samling praktiska guider om vardagliga ämnen.', mission: 'Vårt uppdrag', missionText: 'Vi tror att alla förtjänar tillgång till tydlig, praktisk information.' },
  }

  const t = content[lang] ?? content.en

  return (
    <div style={{ maxWidth: '680px', margin: '0 auto', padding: '32px 16px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 500, marginBottom: '16px' }}>{t.title}</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '28px', lineHeight: 1.7, fontSize: '16px' }}>{t.body}</p>
      <div style={{ borderLeft: '2px solid var(--border)', paddingLeft: '16px' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 500, marginBottom: '8px' }}>{t.mission}</h2>
        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7 }}>{t.missionText}</p>
      </div>
    </div>
  )
}
