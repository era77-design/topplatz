export const runtime = 'edge'

export default function PrivacyPage({ params }) {
  const { lang } = params

  const content = {
    en: {
      title: 'Privacy Policy',
      updated: 'Last updated: June 2026',
      intro: 'This Privacy Policy describes how TopPlatz ("we", "us") collects and uses information when you visit topplatz.com.',
      sections: [
        { h: 'Information We Collect', p: 'We collect anonymous usage data through Google Analytics 4, including pages visited, time on site, and general location (country/city level). We do not collect names, emails, or personal information unless you contact us.' },
        { h: 'Advertising', p: 'We use Google AdSense to display advertisements. Google may use cookies to show relevant ads based on your browsing history. You can opt out at google.com/settings/ads.' },
        { h: 'Cookies', p: 'Our site uses cookies for analytics and advertising purposes. By using this site, you consent to the use of cookies. You can disable cookies in your browser settings.' },
        { h: 'Third Party Links', p: 'Our articles may contain links to third-party websites. We are not responsible for the privacy practices of those sites.' },
        { h: 'Contact Us', p: 'If you have questions about this Privacy Policy, please contact us at: privacy@topplatz.com' },
      ]
    },
    de: {
      title: 'Datenschutzrichtlinie',
      updated: 'Zuletzt aktualisiert: Juni 2026',
      intro: 'Diese Datenschutzrichtlinie beschreibt, wie TopPlatz Informationen sammelt und verwendet.',
      sections: [
        { h: 'Gesammelte Informationen', p: 'Wir erfassen anonyme Nutzungsdaten über Google Analytics 4, einschließlich besuchter Seiten und allgemeinem Standort. Wir erfassen keine persönlichen Daten.' },
        { h: 'Werbung', p: 'Wir verwenden Google AdSense für Werbung. Google kann Cookies verwenden, um relevante Anzeigen zu schalten. Sie können sich unter google.com/settings/ads abmelden.' },
        { h: 'Cookies', p: 'Unsere Website verwendet Cookies für Analyse- und Werbezwecke. Durch die Nutzung dieser Website stimmen Sie der Verwendung von Cookies zu.' },
        { h: 'Links zu Dritten', p: 'Unsere Artikel können Links zu Websites Dritter enthalten. Wir sind nicht verantwortlich für deren Datenschutzpraktiken.' },
        { h: 'Kontakt', p: 'Bei Fragen zur Datenschutzrichtlinie kontaktieren Sie uns: privacy@topplatz.com' },
      ]
    },
    nl: {
      title: 'Privacybeleid',
      updated: 'Laatst bijgewerkt: juni 2026',
      intro: 'Dit privacybeleid beschrijft hoe TopPlatz informatie verzamelt en gebruikt.',
      sections: [
        { h: 'Verzamelde informatie', p: 'We verzamelen anonieme gebruiksgegevens via Google Analytics 4. We verzamelen geen persoonlijke informatie.' },
        { h: 'Advertenties', p: 'We gebruiken Google AdSense voor advertenties. Google kan cookies gebruiken om relevante advertenties te tonen.' },
        { h: 'Cookies', p: 'Onze site gebruikt cookies voor analyse en advertenties. Door deze site te gebruiken, stemt u in met het gebruik van cookies.' },
        { h: 'Links naar derden', p: 'Onze artikelen kunnen links bevatten naar websites van derden. We zijn niet verantwoordelijk voor hun privacypraktijken.' },
        { h: 'Contact', p: 'Voor vragen over dit privacybeleid: privacy@topplatz.com' },
      ]
    },
    sv: {
      title: 'Integritetspolicy',
      updated: 'Senast uppdaterad: juni 2026',
      intro: 'Denna integritetspolicy beskriver hur TopPlatz samlar in och använder information.',
      sections: [
        { h: 'Information vi samlar in', p: 'Vi samlar in anonym användningsdata via Google Analytics 4. Vi samlar inte in personlig information.' },
        { h: 'Annonsering', p: 'Vi använder Google AdSense för annonser. Google kan använda cookies för att visa relevanta annonser.' },
        { h: 'Cookies', p: 'Vår webbplats använder cookies för analys och annonsering. Genom att använda denna webbplats godkänner du användningen av cookies.' },
        { h: 'Tredjepartslänkar', p: 'Våra artiklar kan innehålla länkar till tredjepartswebbplatser. Vi ansvarar inte för deras integritetspraxis.' },
        { h: 'Kontakta oss', p: 'För frågor om denna integritetspolicy: privacy@topplatz.com' },
      ]
    }
  }

  const t = content[lang] ?? content.en

  return (
    <main className="max-w-3xl mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold mb-2">{t.title}</h1>
      <p className="text-gray-500 mb-8">{t.updated}</p>
      <p className="mb-8 text-gray-700">{t.intro}</p>
      {t.sections.map((s, i) => (
        <div key={i} className="mb-6">
          <h2 className="text-xl font-semibold mb-2">{s.h}</h2>
          <p className="text-gray-700">{s.p}</p>
        </div>
      ))}
    </main>
  )
}