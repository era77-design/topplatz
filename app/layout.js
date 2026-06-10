import './globals.css'
import Link from 'next/link'

export const metadata = {
  title: 'TopPlatz — How-To Guides',
  description: 'Step by step guides for everything',
}

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <nav className="border-b px-4 py-3 flex gap-6 text-sm items-center">
          <Link href="/en" className="font-bold text-lg">TopPlatz</Link>
          <Link href="/en/about" className="text-gray-600 hover:text-black">About</Link>
          <Link href="/en/contact" className="text-gray-600 hover:text-black">Contact</Link>
          <Link href="/en/privacy" className="text-gray-600 hover:text-black">Privacy</Link>
        </nav>
        {children}
      </body>
    </html>
  )
}