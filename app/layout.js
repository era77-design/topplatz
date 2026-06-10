import './globals.css'
import Navbar from '@/components/Navbar'
import BottomBar from '@/components/BottomBar'

export const metadata = {
  title: 'TopPlatz — How-To Guides',
  description: 'Step by step guides for everything',
}

export default function RootLayout({ children }) {
  return (
    <html suppressHydrationWarning>
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
        <main style={{ paddingBottom: '70px' }}>
          {children}
        </main>
        <BottomBar />
      </body>
    </html>
  )
}