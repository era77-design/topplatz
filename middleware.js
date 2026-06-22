import { NextResponse } from 'next/server'
const LOCALES = ['en', 'de', 'nl', 'sv']
const DEFAULT_LOCALE = 'en'
export function middleware(request) {
  const { pathname } = request.nextUrl
  const hasLocale = LOCALES.some(
    locale => pathname.startsWith(`/${locale}/`) || pathname === `/${locale}`
  )
  if (hasLocale) return NextResponse.next()
  return NextResponse.redirect(
    new URL(`/${DEFAULT_LOCALE}${pathname}`, request.url)
  )
}
export const config = {
  matcher: ['/((?!_next|favicon.ico|robots.txt|sitemap.xml|ads.txt).*)']
}
