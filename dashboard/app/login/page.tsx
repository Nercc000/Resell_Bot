
"use client"

import { useState } from 'react'
// import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'
// Note: We can use createBrowserClient from @supabase/ssr too, but easiest is usually just standard client if we have it. 
// Let's use the one we already have in lib/supabase.ts for client-side
import { supabase } from '@/lib/supabase'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Loader2, ShieldCheck, Mail } from "lucide-react"

export default function LoginPage() {
    const [email, setEmail] = useState('')
    const [loading, setLoading] = useState(false)
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setMessage(null)

        try {
            const { error } = await supabase.auth.signInWithOtp({
                email,
                options: {
                    // Redirect back to dashboard after login
                    emailRedirectTo: `${window.location.origin}/auth/callback`,
                },
            })

            if (error) {
                setMessage({ type: 'error', text: error.message })
            } else {
                setMessage({
                    type: 'success',
                    text: 'Login-Link gesendet! Bitte prüfe deine E-Mails.'
                })
            }
        } catch (error) {
            setMessage({ type: 'error', text: 'Ein unerwarteter Fehler ist aufgetreten.' })
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-950 p-4">
            <Card className="w-full max-w-md border-gray-800 bg-gray-900/50 backdrop-blur">
                <CardHeader className="space-y-1">
                    <div className="flex justify-center mb-4">
                        <div className="p-3 rounded-full bg-blue-500/10">
                            <ShieldCheck className="w-8 h-8 text-blue-500" />
                        </div>
                    </div>
                    <CardTitle className="text-2xl text-center font-bold">Admin Login</CardTitle>
                    <CardDescription className="text-center">
                        Gib deine E-Mail ein, um dich anzumelden.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleLogin} className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="email">Email</Label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                                <Input
                                    id="email"
                                    type="email"
                                    placeholder="admin@example.com"
                                    className="pl-9 bg-gray-900 border-gray-700"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                />
                            </div>
                        </div>

                        {message && (
                            <Alert variant={message.type === 'error' ? "destructive" : "default"} className={message.type === 'success' ? "border-green-500/50 bg-green-500/10 text-green-500" : ""}>
                                <AlertTitle>{message.type === 'error' ? 'Fehler' : 'Erfolg'}</AlertTitle>
                                <AlertDescription>
                                    {message.text}
                                </AlertDescription>
                            </Alert>
                        )}

                        <Button className="w-full" type="submit" disabled={loading}>
                            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            {loading ? 'Sende Link...' : 'Login-Link senden'}
                        </Button>
                    </form>
                </CardContent>
                <CardFooter className="flex justify-center">
                    <p className="text-xs text-muted-foreground">Geschützter Bereich für Resell Bot</p>
                </CardFooter>
            </Card>
        </div>
    )
}
