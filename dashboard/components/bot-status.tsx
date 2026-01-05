"use client"

import * as React from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Play, Square, RefreshCcw } from "lucide-react"

export function BotStatus() {
    const [status, setStatus] = React.useState<"idle" | "running" | "error">("idle")

    const [isLoading, setIsLoading] = React.useState(false)

    const handleStart = async (mode: string = "full") => {
        if (isLoading) return
        setIsLoading(true)
        try {
            await fetch('/api/bot/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode })
            })
            setStatus("running")
        } catch (e) {
            console.error(e)
        } finally {
            setIsLoading(false)
        }
    }

    const handleStop = async () => {
        if (isLoading) return
        setIsLoading(true)
        try {
            await fetch('/api/bot/stop', { method: 'POST' })
            setStatus("idle")
        } catch (e) {
            console.error(e)
        } finally {
            setIsLoading(false)
        }
    }

    // Poll status
    React.useEffect(() => {
        const checkStatus = async () => {
            try {
                const res = await fetch('/api/bot/status')
                const data = await res.json()
                // Nur Status updaten wenn wir nicht gerade selbst was triggern
                if (!isLoading) {
                    setStatus(data.status as any)
                }
            } catch (e) { }
        }
        checkStatus()
        const interval = setInterval(checkStatus, 5000)
        return () => clearInterval(interval)
    }, [isLoading])

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Bot Status</CardTitle>
                <Badge variant={status === "running" ? "default" : "secondary"}>
                    {status === "running" ? "Running" : "Idle"}
                </Badge>
            </CardHeader>
            <CardContent>
                <div className="flex flex-col space-y-2">
                    {status === "idle" ? (
                        <>
                            <Button className="w-full" onClick={() => handleStart("full")} disabled={isLoading}>
                                <Play className="mr-2 h-4 w-4" />
                                {isLoading ? "Starte..." : "Start Komplett"}
                            </Button>
                            <div className="flex space-x-2">
                                <Button variant="outline" className="w-1/2" onClick={() => handleStart("scrape")} disabled={isLoading}>
                                    <RefreshCcw className="mr-2 h-4 w-4" />
                                    {isLoading ? "..." : "Nur Scrapen"}
                                </Button>
                                <Button variant="outline" className="w-1/2" onClick={() => handleStart("send")} disabled={isLoading}>
                                    <Play className="mr-2 h-4 w-4" />
                                    {isLoading ? "..." : "Nur Senden"}
                                </Button>
                            </div>
                            <Button variant="secondary" className="w-full mt-2" onClick={() => handleStart("debug")} disabled={isLoading}>
                                <Play className="mr-2 h-4 w-4" />
                                {isLoading ? "..." : "DEBUG START (Minimal)"}
                            </Button>
                        </>
                    ) : (
                        <Button variant="destructive" className="w-full" onClick={handleStop} disabled={isLoading}>
                            <Square className="mr-2 h-4 w-4" /> Stop Bot
                        </Button>
                    )}
                </div>
            </CardContent>
        </Card>
    )
}
