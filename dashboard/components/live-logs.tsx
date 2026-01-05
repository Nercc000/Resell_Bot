"use client"

import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Trash2, CheckCircle2, XCircle, AlertTriangle, Info, Mail, Cookie, Globe, Loader2, Send, Search, Database, Zap } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

type LogType = 'success' | 'error' | 'warning' | 'info' | 'action' | 'system'

interface ParsedLog {
    time: string
    message: string
    type: LogType
    icon: React.ReactNode
    cleanMessage: string
}

// Parse emoji/text patterns to determine log type and icon
function parseLog(time: string, message: string): ParsedLog {
    const msg = message.toLowerCase()

    // Success patterns
    if (msg.includes('✅') || msg.includes('gesendet') || msg.includes('erfolgreich') || msg.includes('eingeloggt')) {
        return { time, message, type: 'success', icon: <CheckCircle2 className="h-4 w-4" />, cleanMessage: message.replace(/[✅🎉]/g, '').trim() }
    }

    // Error patterns
    if (msg.includes('❌') || msg.includes('fehler') || msg.includes('failed') || msg.includes('error')) {
        return { time, message, type: 'error', icon: <XCircle className="h-4 w-4" />, cleanMessage: message.replace(/[❌]/g, '').trim() }
    }

    // Warning patterns
    if (msg.includes('⚠️') || msg.includes('warnung') || msg.includes('überspringe') || msg.includes('⏩')) {
        return { time, message, type: 'warning', icon: <AlertTriangle className="h-4 w-4" />, cleanMessage: message.replace(/[⚠️⏩]/g, '').trim() }
    }

    // Action patterns
    if (msg.includes('📨') || msg.includes('senden') || msg.includes('nachricht')) {
        return { time, message, type: 'action', icon: <Send className="h-4 w-4" />, cleanMessage: message.replace(/[📨📬]/g, '').trim() }
    }

    // Cookie/Login patterns
    if (msg.includes('🍪') || msg.includes('cookie') || msg.includes('🔐') || msg.includes('login')) {
        return { time, message, type: 'system', icon: <Cookie className="h-4 w-4" />, cleanMessage: message.replace(/[🍪🔐]/g, '').trim() }
    }

    // Database patterns
    if (msg.includes('💾') || msg.includes('supabase') || msg.includes('db') || msg.includes('📊')) {
        return { time, message, type: 'info', icon: <Database className="h-4 w-4" />, cleanMessage: message.replace(/[💾📊📡]/g, '').trim() }
    }

    // Search/Scrape patterns
    if (msg.includes('🔍') || msg.includes('scrape') || msg.includes('suche') || msg.includes('📋')) {
        return { time, message, type: 'info', icon: <Search className="h-4 w-4" />, cleanMessage: message.replace(/[🔍📋]/g, '').trim() }
    }

    // Loading/Process patterns
    if (msg.includes('⏳') || msg.includes('🚀') || msg.includes('starte') || msg.includes('lade')) {
        return { time, message, type: 'system', icon: <Loader2 className="h-4 w-4 animate-spin" />, cleanMessage: message.replace(/[⏳🚀]/g, '').trim() }
    }

    // Default info
    return { time, message, type: 'info', icon: <Info className="h-4 w-4" />, cleanMessage: message.replace(/[📧🌍📁📱🆕ℹ️]/g, '').trim() }
}

const typeStyles: Record<LogType, string> = {
    success: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
    error: 'bg-red-500/10 border-red-500/30 text-red-400',
    warning: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
    info: 'bg-blue-500/10 border-blue-500/30 text-blue-400',
    action: 'bg-purple-500/10 border-purple-500/30 text-purple-400',
    system: 'bg-slate-500/10 border-slate-500/30 text-slate-400',
}

const iconStyles: Record<LogType, string> = {
    success: 'text-emerald-400',
    error: 'text-red-400',
    warning: 'text-amber-400',
    info: 'text-blue-400',
    action: 'text-purple-400',
    system: 'text-slate-400',
}

export function LiveLogs() {
    const [logs, setLogs] = React.useState<ParsedLog[]>([])
    const [connected, setConnected] = React.useState(false)
    const [filter, setFilter] = React.useState<LogType | 'all'>('all')

    const clearLogs = () => setLogs([])

    React.useEffect(() => {
        const hostname = window.location.hostname
        const wsUrl = `ws://${hostname}:8000/api/ws/logs`

        let ws: WebSocket | null = null
        let retryTimeout: NodeJS.Timeout

        const connect = () => {
            if (typeof window === 'undefined') return

            try {
                ws = new WebSocket(wsUrl)
            } catch (e) {
                return
            }

            ws.onopen = () => setConnected(true)

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data)
                    const msg = data.message?.trim() || ''

                    // Skip ugly separator lines and empty messages
                    if (!msg || msg.match(/^[=\-_]{5,}$/) || msg === '') {
                        return
                    }

                    const now = new Date().toLocaleTimeString([], { hour12: false })
                    const parsed = parseLog(now, msg)
                    setLogs(prev => [parsed, ...prev].slice(0, 100))
                } catch (e) { }
            }

            ws.onclose = () => {
                setConnected(false)
                retryTimeout = setTimeout(connect, 3000)
            }
        }

        connect()

        return () => {
            if (ws) ws.close()
            clearTimeout(retryTimeout)
        }
    }, [])

    const filteredLogs = filter === 'all' ? logs : logs.filter(l => l.type === filter)

    const counts = {
        success: logs.filter(l => l.type === 'success').length,
        error: logs.filter(l => l.type === 'error').length,
        warning: logs.filter(l => l.type === 'warning').length,
    }

    return (
        <Card className="col-span-3 bg-gradient-to-br from-background to-muted/20 backdrop-blur-sm border-muted/50">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                        <Zap className="h-5 w-5 text-primary" />
                        <CardTitle className="text-base font-semibold">Activity Feed</CardTitle>
                    </div>
                    <div className={cn(
                        "flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium transition-all",
                        connected
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                            : "bg-red-500/10 text-red-400 border border-red-500/30 animate-pulse"
                    )}>
                        <div className={cn("h-1.5 w-1.5 rounded-full", connected ? "bg-emerald-400" : "bg-red-400")} />
                        {connected ? "Live" : "Offline"}
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    {counts.error > 0 && (
                        <Badge variant="outline" className="bg-red-500/10 border-red-500/30 text-red-400 text-xs">
                            {counts.error} Fehler
                        </Badge>
                    )}
                    {counts.success > 0 && (
                        <Badge variant="outline" className="bg-emerald-500/10 border-emerald-500/30 text-emerald-400 text-xs">
                            {counts.success} OK
                        </Badge>
                    )}
                    <Button variant="ghost" size="icon" onClick={clearLogs} className="h-8 w-8 text-muted-foreground hover:text-foreground">
                        <Trash2 className="h-4 w-4" />
                    </Button>
                </div>
            </CardHeader>
            <CardContent className="pt-0">
                {/* Filter Pills */}
                <div className="flex gap-1.5 mb-3 flex-wrap">
                    {(['all', 'success', 'error', 'warning', 'action', 'info'] as const).map((type) => (
                        <button
                            key={type}
                            onClick={() => setFilter(type)}
                            className={cn(
                                "px-2.5 py-1 rounded-full text-xs font-medium transition-all",
                                filter === type
                                    ? "bg-primary text-primary-foreground"
                                    : "bg-muted/50 text-muted-foreground hover:bg-muted hover:text-foreground"
                            )}
                        >
                            {type === 'all' ? 'Alle' : type.charAt(0).toUpperCase() + type.slice(1)}
                        </button>
                    ))}
                </div>

                <ScrollArea className="h-[280px] w-full rounded-lg border border-muted/50 bg-black/20 p-3">
                    <div className="space-y-2">
                        {filteredLogs.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-[200px] text-muted-foreground">
                                <Loader2 className="h-8 w-8 animate-spin mb-2 opacity-50" />
                                <span className="text-sm">Warte auf Bot-Aktivität...</span>
                            </div>
                        ) : (
                            filteredLogs.map((log, index) => (
                                <div
                                    key={index}
                                    className={cn(
                                        "flex items-start gap-3 p-2.5 rounded-lg border transition-all animate-in fade-in slide-in-from-top-2 duration-300",
                                        typeStyles[log.type]
                                    )}
                                    style={{ animationDelay: `${index * 20}ms` }}
                                >
                                    <div className={cn("mt-0.5 shrink-0", iconStyles[log.type])}>
                                        {log.icon}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm leading-snug break-words">
                                            {log.cleanMessage}
                                        </p>
                                    </div>
                                    <span className="text-[10px] text-muted-foreground shrink-0 tabular-nums">
                                        {log.time}
                                    </span>
                                </div>
                            ))
                        )}
                    </div>
                </ScrollArea>
            </CardContent>
        </Card>
    )
}
