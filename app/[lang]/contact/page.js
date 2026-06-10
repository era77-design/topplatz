export const runtime = 'edge'

export default function ContactPage({ params }) {
  const { lang } = params

  const content = {
    en: { title: 'Contact Us', text: 'Have a question or suggestion? We\'d love to hear from you.', label: 'General inquiries:' },
    de: { title: 'Kontakt', text: 'Haben Sie eine Frage? Wir freuen uns von Ihnen zu hören.', label: 'Allgemeine Anfragen:' },
    nl: { title: 'Contact', text: 'Heeft u een vraag? We horen graag van u.', label: 'Algemene vragen:' },
    sv: { title: 'Kontakta oss', text: 'Har du en fråga? Vi hör gärna från dig.', label: 'Allmänna frågor:' },
  }

  const t = content[lang] ?? content.en

  return (
    <div style={{ maxWidth: '680px', margin: '0 auto', padding: '32px 16px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 500, marginBottom: '12px' }}>{t.title}</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '24px', lineHeight: 1.6 }}>{t.text}</p>
      <div style={{
        background: 'var(--bg-secondary)',
        border: '0.5px solid var(--border)',
        borderRadius: '12px',
        padding: '20px',
      }}>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '8px' }}>{t.label}</p>
        <a href="mailto:contact@topplatz.com" style={{ color: 'var(--text)', fontWeight: 500 }}>
          contact@topplatz.com
        </a>
      </div>
    </div>
  )
}