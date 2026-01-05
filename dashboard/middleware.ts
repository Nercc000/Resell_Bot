
import { createServerClient, type CookieOptions } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
    let response = NextResponse.next({
        request: {
            headers: request.headers,
        },
    })

    // Create an authenticated Supabase Client
    const supabase = createServerClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
        {
            cookies: {
                get(name: string) {
                    return request.cookies.get(name)?.value
                },
                set(name: string, value: string, options: CookieOptions) {
                    request.cookies.set({
                        name,
                        value,
                        ...options,
                    })
                    response = NextResponse.next({
                        request: {
                            headers: request.headers,
                        },
                    })
                    response.cookies.set({
                        name,
                        value,
                        ...options,
                    })
                },
                remove(name: string, options: CookieOptions) {
                    request.cookies.set({
                        name,
                        value: '',
                        ...options,
                    })
                    response = NextResponse.next({
                        request: {
                            headers: request.headers,
                        },
                    })
                    response.cookies.set({
                        name,
                        value: '',
                        ...options,
                    })
                },
            },
        }
    )

    // Refresh session if expired
    const { data: { user } } = await supabase.auth.getUser()

    // ROUTE PROTECTION LOGIC
    const adminEmail = "digga9286@gmail.com"

    // If no user and asking for protected route -> Redirect to Login
    if (!user && !request.nextUrl.pathname.startsWith('/login') && !request.nextUrl.pathname.startsWith('/auth')) {
        return NextResponse.redirect(new URL('/login', request.url))
    }

    // SECURITY: Whitelist Check
    if (user && user.email !== adminEmail) {
        // Log out unauthorized user (by clearing cookies manually or just redirecting with error)
        // Proper way: Redirect to a page that says "Unauthorized" or just back to login with error
        // We can't easily sign them out in middleware without calling an endpoint, so we destroy the cookies in the response
        const url = new URL('/login', request.url)
        url.searchParams.set('error', 'unauthorized_email')

        const resp = NextResponse.redirect(url)
        // Clear auth cookies
        resp.cookies.set('sb-access-token', '', { maxAge: 0 })
        resp.cookies.set('sb-refresh-token', '', { maxAge: 0 })
        // Also clear project-specific cookie names if any (supabase-ssr usually uses sb-<ref>-auth-token)
        // We'll rely on the client to handle the error state too
        return resp
    }

    // If user exists and is on /login -> Redirect to Dashboard
    if (user && request.nextUrl.pathname.startsWith('/login')) {
        return NextResponse.redirect(new URL('/', request.url))
    }

    return response
}

export const config = {
    matcher: [
        /*
         * Match all request paths except for the ones starting with:
         * - _next/static (static files)
         * - _next/image (image optimization files)
         * - favicon.ico (favicon file)
         * - api/bot (Allow API access for public endpoints if needed, OR protect them too? Let's protect them for security)
         * Actually: API routes used by the frontend need cookies passed. External access needs logic. 
         * User wants 'dashboard' protected.
         * Let's exclude Next internals and static assets.
         */
        '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
    ],
}
