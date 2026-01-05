
"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ShieldAlert } from "lucide-react"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"

export default function AuthErrorPage() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-950 p-4">
            <Card className="w-full max-w-md border-red-900/50 bg-gray-900/50 backdrop-blur">
                <CardHeader className="space-y-1">
                    <div className="flex justify-center mb-4">
                        <div className="p-3 rounded-full bg-red-500/10">
                            <ShieldAlert className="w-8 h-8 text-red-500" />
                        </div>
                    </div>
                    <CardTitle className="text-2xl text-center font-bold text-red-500">Login fehlgeschlagen</CardTitle>
                </CardHeader>
                <CardContent className="text-center text-gray-400 space-y-4">
                    <p>
                        Der Login-Link ist ungültig oder abgelaufen.
                    </p>
                    <p className="text-sm">
                        Das passiert oft, wenn man an den URL-Einstellungen Änderungen vorgenommen hat und noch einen "alten" Link benutzt.
                    </p>
                </CardContent>
                <CardFooter className="flex justify-center">
                    <Button asChild variant="secondary">
                        <Link href="/login">Neuen Link anfordern</Link>
                    </Button>
                </CardFooter>
            </Card>
        </div>
    )
}
