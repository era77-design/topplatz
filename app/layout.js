import './globals.css'
import Navbar from '@/components/Navbar'
import BottomBar from '@/components/BottomBar'
import CookieBanner from '@/components/CookieBanner'
import Footer from '@/components/Footer'

export const metadata = {
  title: 'TopPlatz — How-To Guides',
  description: 'Step by step guides for everything',
}

// viewport-fit=cover обязателен для env(safe-area-inset-bottom) на iOS —
// без него safe-area не работает и BottomBar перекрывает home indicator
export const viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
}

export default function RootLayout({ children }) {
  return (
    <html suppressHydrationWarning>
      <head>
        <style>{`
          body {
            /* Предотвращает резиновый оверскролл на iOS Safari — именно он
               вызывает "уплыв" fixed-элементов при bounce-эффекте */
            overscroll-behavior-y: none;
          }
        `}</style>
      </head>
      <body>
        <script dangerouslySetInnerHTML={{
          __html: `
            (function() {
              const t = localStorage.getItem('theme') || 'light';
              document.documentElement.setAttribute('data-theme', t);
            })();
          `
        }} />
        <Navbar />
        {/* calc учитывает высоту BottomBar (60px) + safe-area iOS (home indicator) */}
        <main style={{ paddingBottom: 'calc(70px + env(safe-area-inset-bottom, 0px))' }}>
          {children}
        </main>
        <Footer />
        <BottomBar />
        <CookieBanner />
      </body>
    </html>
  )
}