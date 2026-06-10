export const runtime = 'edge'

export default function ContactPage({ params }) {
  const { lang } = params

  const content = {
    en: { title: 'Contact Us',    text: 'Have a question or suggestion? We\'d love to hear from you.', email: 'Email us at:', label: 'General inquiries:' },
    de: { title: 'Kontakt',       text: 'Haben Sie eine Frage oder einen Vorschlag? Wir freuen uns von Ihnen zu hören.', email: 'Schreiben Sie uns:', label: 'Allgemeine Anfragen:' },
    nl: { title: 'Contact',       text: 'Heeft u een vraag of suggestie? We horen graag van u.', email: 'E-mail ons:', label: 'Algemene vragen:' },
    sv: { title: 'Kontakta oss',  text: 'Har du en fråga eller ett förslag? Vi hör gärna från dig.', email: 'Maila oss:', label: 'Allmänna frågor:' },
  }

  const t = content[lang] ?? content.en

  return (
    <main className="max-w-3xl mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold mb-6">{t.title}</h1>
      <p className="text-gray-700 mb-8">{t.text}</p>
      <div className="bg-gray-50 rounded-lg p-6">
        <p className="font-semibold mb-1">{t.label}</p>
        <a href="mailto:contact@topplatz.com" className="text-blue-600 hover:underline">
          contact@topplatz.com
        </a>
      </div>
    </main>
  )
}