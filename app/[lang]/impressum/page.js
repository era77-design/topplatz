export const runtime = 'edge'

export async function generateMetadata({ params }) {
  const { lang } = await params
  const titles = {
    en: 'Legal Notice — TopPlatz',
    de: 'Impressum — TopPlatz',
    nl: 'Colofon — TopPlatz',
    sv: 'Juridisk information — TopPlatz',
  }
  return { title: titles[lang] || titles.de }
}

export default async function ImpressumPage({ params }) {
  const { lang } = await params

  const content = {
    en: {
      title: 'Legal Notice',
      owner: 'Website Owner',
      contact: 'Contact',
      responsibility: 'Responsible for content',
      disclaimer: 'Disclaimer',
      disclaimerText: 'The content of this website has been created with the utmost care. However, we cannot guarantee the accuracy, completeness or topicality of the content. As a service provider we are responsible for our own content on these pages according to general law. We are not obliged to monitor transmitted or stored third-party information.',
      eu: 'EU Dispute Resolution',
      euText: 'The European Commission provides a platform for online dispute resolution (ODR): https://ec.europa.eu/consumers/odr. Our email address can be found above. We are not willing or obliged to participate in dispute resolution proceedings before a consumer arbitration board.',
    },
    de: {
      title: 'Impressum',
      owner: 'Websitebetreiber',
      contact: 'Kontakt',
      responsibility: 'Verantwortlich für den Inhalt',
      disclaimer: 'Haftungsausschluss',
      disclaimerText: 'Die Inhalte unserer Seiten wurden mit größter Sorgfalt erstellt. Für die Richtigkeit, Vollständigkeit und Aktualität der Inhalte können wir jedoch keine Gewähr übernehmen. Als Diensteanbieter sind wir gemäß § 7 Abs.1 TMG für eigene Inhalte auf diesen Seiten nach den allgemeinen Gesetzen verantwortlich.',
      eu: 'EU-Streitschlichtung',
      euText: 'Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit: https://ec.europa.eu/consumers/odr. Unsere E-Mail-Adresse finden Sie oben im Impressum. Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.',
    },
    nl: {
      title: 'Colofon',
      owner: 'Websitebeheerder',
      contact: 'Contact',
      responsibility: 'Verantwoordelijk voor de inhoud',
      disclaimer: 'Disclaimer',
      disclaimerText: 'De inhoud van deze website is met de grootst mogelijke zorg samengesteld. Wij kunnen echter geen garantie geven voor de juistheid, volledigheid en actualiteit van de inhoud.',
      eu: 'EU-geschillenbeslechting',
      euText: 'De Europese Commissie biedt een platform voor onlinegeschillenbeslechting (ODR): https://ec.europa.eu/consumers/odr.',
    },
    sv: {
      title: 'Juridisk information',
      owner: 'Webbplatsägare',
      contact: 'Kontakt',
      responsibility: 'Ansvarig för innehåll',
      disclaimer: 'Ansvarsfriskrivning',
      disclaimerText: 'Innehållet på denna webbplats har skapats med största omsorg. Vi kan dock inte garantera riktigheten, fullständigheten eller aktualiteten hos innehållet.',
      eu: 'EU:s tvistlösning online',
      euText: 'EU-kommissionen tillhandahåller en plattform för onlinetvistlösning: https://ec.europa.eu/consumers/odr.',
    },
  }

  const t = content[lang] ?? content.de

  const sectionStyle = {
    marginBottom: '28px',
  }
  const labelStyle = {
    fontSize: '12px',
    fontWeight: 500,
    color: 'var(--text-secondary)',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    marginBottom: '6px',
  }
  const valueStyle = {
    fontSize: '15px',
    color: 'var(--text)',
    lineHeight: 1.7,
  }

  return (
    <div style={{ maxWidth: '680px', margin: '0 auto', padding: '32px 16px 64px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 500, marginBottom: '8px' }}>{t.title}</h1>
      <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '32px' }}>
        {lang === 'de' ? 'Angaben gemäß § 5 TMG' : 'Legal information'}
      </p>

      <div style={sectionStyle}>
        <p style={labelStyle}>{t.owner}</p>
        <p style={valueStyle}>TopPlatz</p>
      </div>

      <div style={sectionStyle}>
        <p style={labelStyle}>{t.contact}</p>
        <p style={valueStyle}>
          E-Mail:{' '}
          <a href="mailto:contact@topplatz.com" style={{ color: 'var(--text)', textDecoration: 'underline' }}>
            contact@topplatz.com
          </a>
        </p>
      </div>

      <div style={sectionStyle}>
        <p style={labelStyle}>{t.responsibility}</p>
        <p style={valueStyle}>TopPlatz<br />contact@topplatz.com</p>
      </div>

      <hr style={{ border: 'none', borderTop: '0.5px solid var(--border)', margin: '32px 0' }} />

      <div style={sectionStyle}>
        <h2 style={{ fontSize: '17px', fontWeight: 500, marginBottom: '8px', color: 'var(--text)' }}>
          {t.disclaimer}
        </h2>
        <p style={{ ...valueStyle, color: 'var(--text-secondary)', fontSize: '14px' }}>
          {t.disclaimerText}
        </p>
      </div>

      <div style={sectionStyle}>
        <h2 style={{ fontSize: '17px', fontWeight: 500, marginBottom: '8px', color: 'var(--text)' }}>
          {t.eu}
        </h2>
        <p style={{ ...valueStyle, color: 'var(--text-secondary)', fontSize: '14px' }}>
          {t.euText}
        </p>
      </div>
    </div>
  )
}
