import './globals.css'

export const metadata = {
  title: 'TopPlatz — How-To Guides',
  description: 'Step by step guides for everything',
}

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <nav className="border-b px-4 py-3 flex gap-6 text-sm">
          <a href="/" className="font-bold text-lg">TopPlatz</a>
          <a href="./about" className="text-gray-600 hover:text-black">About</a>
          <a href="./contact" className="text-gray-600 hover:text-black">Contact</a>
          <a href="./privacy" className="text-gray-600 hover:text-black">Privacy</a>
        </nav>
        {children}
      </body>
    </html>
  )
}