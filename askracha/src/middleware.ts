import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname

  if (path === '/') {
    const sessionId = request.cookies.get('askracha-session-id')?.value
    if (sessionId) {
      return NextResponse.redirect(new URL(`/chat/${sessionId}`, request.url))
    }
    return NextResponse.redirect(new URL('/chat', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/']
}
