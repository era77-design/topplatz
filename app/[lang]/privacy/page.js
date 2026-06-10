export const runtime = 'edge'

export default function PrivacyPage({ params }) {
  const { lang } = params

  const content = {
    en: {
      title: 'Privacy Policy',
      updated: 'Last updated: June 2026',
      intro: 'This Privacy Policy describes how TopPlatz collects and uses information when you visit topplatz.com.',
      sections: [
        { h: 'Information We Collect', p: 'We collect anonymous usage data through Google Analytics 4, including pages visited and general location. We do not collect names, emails, or personal information.' },
        { h: 'Advertising', p: 'We use Google AdSense to display advertisements. Google may use cookies to show relevant ads. You can opt out at google.com/settings/ads.' },
        { h: 'Cookies', p: 'Our site uses cookies for analytics and advertising. By using this site, you consent to cookies. You can disable them in your browser settings.' },
        { h: 'Third Party Links', p: 'Our articles may contain links to third-party websites. We are not responsible for their privacy practices.' },
        { h: 'Contact', p: 'Questions? Email us at: privacy@topplatz.com' },
      ]
    },
    de: {
      title: 'Datenschutzrichtlinie',
      updated: 'Zuletzt aktualisiert: Juni 2026',
      intro: 'Diese Datenschutzrichtlinie beschreibt, wie TopPlatz Informationen sammelt und verwendet.',
      sections: [
        { h: 'Gesammelte Informationen', p: 'Wir erfassen anonyme Nutzungsdaten über Google Analytics 4. Wir erfassen keine persönlichen Daten.' },
        { h: 'Werbung', p: 'Wir verwenden Google AdSense. Sie können sich unter google.com/settings/ads abmelden.' },
        { h: 'Cookies', p: 'Unsere Website verwendet Cookies. Durch die Nutzung stimmen Sie zu.' },
        { h: 'Links zu Dritten', p: 'Wir sind nicht verantwortlich für Datenschutzpraktiken Dritter.' },
        { h: 'Kontakt', p: 'Fragen? E-Mail: privacy@topplatz.com' },
      ]
    },
    nl: {
      title: 'Privacybeleid',
      updated: 'Laatst bijgewerkt: juni 2026',
      intro: 'Dit privacybeleid beschrijft hoe TopPlatz informatie verzamelt en gebruikt.',
      sections: [
        { h: 'Verzamelde informatie', p: 'We verzamelen anonieme gebruiksgegevens via Google Analytics 4.' },
        { h: 'Advertenties', p: 'We gebruiken Google AdSense. U kunt zich afmelden via google.com/settings/ads.' },
        { h: 'Cookies', p: 'Onze site gebruikt cookies. Door de site te gebruiken, stemt u in.' },
        { h: 'Links naar derden', p: 'We zijn niet verantwoordelijk voor privacypraktijken van derden.' },
        { h: 'Contact', p: 'Vragen? E-mail: privacy@topplatz.com' },
      ]
    },
    sv: {
      title: 'Integritetspolicy',
      updated: 'Senast uppdaterad: juni 2026',
      intro: 'Denna policy beskriver hur TopPlatz samlar in och använder information.',
      sections: [
        { h: 'Information vi samlar in', p: 'Vi samlar in anonym data via Google Analytics 4.' },
        { h: 'Annonsering', p: 'Vi använder Google AdSense. Välj bort på google.com/settings/ads.' },
        { h: 'Cookies', p: 'Vår webbplats använder cookies. Genom att använda sidan godkänner du.' },
        { h: 'Tredjepartslänkar', p: 'Vi ansvarar inte för tredjeparters integritetspraxis.' },
        { h: 'Kontakt', p: 'Frågor? E-post: privacy@topplatz.com' },
      ]
    }
  }

  const t = content[lang] ?? content.en

  return (
    <div style={{ maxWidth: '680px', margin: '0 auto', padding: '32px 16px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 500, marginBottom: '6px' }}>{t.title}</h1>
      <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '20px' }}>{t.updated}</p>
      <p style={{ marginBottom: '24px', color: 'var(--text-secondary)', lineHeight: 1.7 }}>{t.intro}</p>
      {t.sections.map((s, i) => (
        <div key={i} style={{ marginBottom: '20px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 500, marginBottom: '6px' }}>{s.h}</h2>
          <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7 }}>{s.p}</p>
        </div>
      ))}
    </div>
  )
}