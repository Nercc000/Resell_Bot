"use client"

import { useEffect, useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { supabase } from '@/lib/supabase'

function CallbackContent() {
    const router = useRouter()
    const searchParams = useSearchParams()
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        const handleCallback = async () => {
            const code = searchParams.get('code')
            const next = searchParams.get('next') ?? '/'

            if (code) {
                const { error } = await supabase.auth.exchangeCodeForSession(code)
                if (!error) {
                    router.push(next)
                } else {
                    console.error("Auth Error:", error)
                    setError(error.message)
                }
            } else {
                router.push('/')
            }
        }

        handleCallback()
    }, [searchParams, router])

    if (error) {
        return (
            <div className="flex min-h-screen flex-col items-center justify-center p-4">
                <div className="text-destructive font-bold mb-4">Authentication Error</div>
                <div className="text-muted-foreground">{error}</div>
            </div>
        )
    }

    return (
        <div className="flex min-h-screen flex-col items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <p className="mt-4 text-muted-foreground">Authenticating...</p>
        </div>
    )
}

export default function AuthCallbackPage() {
    return (
        <Suspense fallback={
            <div className="flex min-h-screen flex-col items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                <p className="mt-4 text-muted-foreground">Loading...</p>
            </div>
        }>
            <CallbackContent />
        </Suspense>
    )
}
