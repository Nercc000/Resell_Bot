"use client"

import { useEffect, useState, useMemo } from "react"
import { supabase } from "@/lib/supabase"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Search, Filter, ShieldCheck, ShieldAlert, RefreshCw, BarChart3, Database } from "lucide-react"
import { Check, X } from "lucide-react"
import Link from "next/link"
import { cn } from "@/lib/utils"

type DebugListing = {
    id: string
    title: string
    price: string
    link: string
    filter_status: string | null
    filter_reason: string | null
    created_at: string
    category: string | null
    session_id: string | null
}

export default function DebugPage() {
    const [listings, setListings] = useState<DebugListing[]>([])
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState("")
    const [statusFilter, setStatusFilter] = useState<'all' | 'passed' | 'rejected'>('all')
    const [selectedSession, setSelectedSession] = useState<string>("all")

    const fetchListings = async () => {
        setLoading(true)
        const { data, error } = await supabase
            .from('listings')
            .select('*')
            .order('created_at', { ascending: false })
            .limit(2000)

        if (error) console.error(error)
        else setListings(data as DebugListing[])
        setLoading(false)
    }

    useEffect(() => {
        fetchListings()
    }, [])

    // Extract unique sessions and format date
    const sessions = useMemo(() => {
        const uniqueSessions = new Set(listings.map(l => l.session_id).filter(Boolean))
        return Array.from(uniqueSessions).map(sid => {
            const firstItem = listings.find(l => l.session_id === sid)
            return {
                id: sid as string,
                date: firstItem ? new Date(firstItem.created_at).toLocaleString() : 'Unknown Date',
                count: listings.filter(l => l.session_id === sid).length
            }
        }).sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()) // sort new to old
    }, [listings])

    // Filter by session
    const currentListings = useMemo(() => {
        if (selectedSession === "all") return listings
        return listings.filter(l => l.session_id === selectedSession)
    }, [listings, selectedSession])

    // Funnel Stats for Current View
    const stats = useMemo(() => {
        const total = currentListings.length
        const passedTitle = currentListings.filter(l => l.filter_status?.includes('passed') || l.filter_status === 'passed_ai_title').length
        const finalPassed = currentListings.filter(l => l.filter_status === 'passed' || l.filter_status?.includes('passed')).length // simplified
        const rejected = currentListings.filter(l => l.filter_status?.includes('rejected')).length

        return { total, passedTitle, finalPassed, rejected }
    }, [currentListings])


    const getStatusBadge = (status: string | null) => {
        if (!status) return <Badge variant="outline" className="text-muted-foreground">Unbekannt</Badge>

        if (status.includes('passed')) {
            return <Badge className="bg-emerald-500/15 text-emerald-500 border-emerald-500/20 hover:bg-emerald-500/25"><Check className="w-3 h-3 mr-1" /> Passed</Badge>
        }
        if (status.includes('rejected')) {
            return <Badge variant="destructive" className="bg-red-500/15 text-red-500 border-red-500/20 hover:bg-red-500/25"><X className="w-3 h-3 mr-1" /> Rejected</Badge>
        }
        return <Badge variant="secondary">{status}</Badge>
    }

    const filtered = currentListings.filter(l => {
        const matchesSearch = l.title.toLowerCase().includes(search.toLowerCase()) ||
            (l.filter_reason && l.filter_reason.toLowerCase().includes(search.toLowerCase()))

        if (statusFilter === 'passed') return matchesSearch && l.filter_status?.includes('passed')
        if (statusFilter === 'rejected') return matchesSearch && l.filter_status?.includes('rejected')
        return matchesSearch
    })

    return (
        <div className="flex min-h-screen flex-col bg-background">

            <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">

                {/* Header Row */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
                    <div>
                        <h1 className="text-2xl font-bold flex items-center gap-2">
                            <Filter className="w-6 h-6 text-purple-500" />
                            Filter Test Pipeline
                        </h1>
                        <p className="text-muted-foreground text-sm">Visualisiere die Filter-Entscheidungen pro Run.</p>
                    </div>

                    <div className="flex items-center gap-2 w-full md:w-auto">
                        <Select value={selectedSession} onValueChange={setSelectedSession}>
                            <SelectTrigger className="w-[280px]">
                                <SelectValue placeholder="Wähle einen Run / Session" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">Alle Runs anzeigen ({listings.length})</SelectItem>
                                {sessions.map(s => (
                                    <SelectItem key={s.id} value={s.id}>
                                        {s.date} ({s.count} Items)
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                        <Button variant="outline" size="sm" onClick={fetchListings} disabled={loading}>
                            <RefreshCw className={cn("w-4 h-4 mr-2", loading && "animate-spin")} />
                            Refresh
                        </Button>
                    </div>
                </div>

                {/* Funnel Visualization */}
                {/* Funnel Visualization */}
                <div className="grid gap-4 md:grid-cols-4 relative">
                    {/* Step 1: Raw */}
                    <Card className="bg-muted/30 border-dashed relative overflow-hidden">
                        <div className="absolute right-0 top-0 p-2 opacity-10"><Database className="w-12 h-12" /></div>
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium flex items-center text-muted-foreground">
                                1. Rohdaten (Scraped)
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold">{stats.total}</div>
                            <p className="text-xs text-muted-foreground">Alle gefundenen Anzeigen</p>
                        </CardContent>
                    </Card>

                    {/* Step 2: Keyword Filter */}
                    <Card className="relative overflow-hidden">
                        <div className="absolute right-0 top-0 p-2 opacity-10"><Filter className="w-12 h-12 text-blue-500" /></div>
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium flex items-center text-blue-600">
                                2. Nach Keyword-Filter
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold text-blue-600">
                                {currentListings.filter(l => !l.filter_status?.includes('rejected_keyword')).length}
                            </div>
                            <p className="text-xs text-muted-foreground">
                                {currentListings.filter(l => l.filter_status?.includes('rejected_keyword')).length} aussortiert (Gesuch/Zubehör)
                            </p>
                        </CardContent>
                    </Card>

                    {/* Step 3: AI Filter */}
                    <Card className="relative overflow-hidden">
                        <div className="absolute right-0 top-0 p-2 opacity-10"><ShieldCheck className="w-12 h-12 text-purple-500" /></div>
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium flex items-center text-purple-600">
                                3. Nach AI-Check
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold text-purple-600">
                                {currentListings.filter(l => l.filter_status?.includes('passed_ai') || l.filter_status === 'passed').length}
                            </div>
                            <p className="text-xs text-muted-foreground">
                                {currentListings.filter(l => l.filter_status?.includes('rejected_ai')).length} aussortiert (Falsche Konsole)
                            </p>
                        </CardContent>
                    </Card>

                    {/* Step 4: Final */}
                    <Card className="bg-emerald-500/5 border-emerald-500/20 relative overflow-hidden">
                        <div className="absolute right-0 top-0 p-2 opacity-10"><Check className="w-12 h-12 text-emerald-500" /></div>
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium flex items-center text-emerald-600">
                                ✅ Final Listings
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold text-emerald-600">{stats.finalPassed}</div>
                            <p className="text-xs text-muted-foreground">Erscheinen im Dashboard</p>
                        </CardContent>
                    </Card>

                </div>


                {/* Filters */}
                <div className="flex gap-4 items-center">
                    <div className="relative flex-1 max-w-sm">
                        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Suche in Titel oder Grund..."
                            className="pl-8"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                    <div className="flex gap-2">
                        <Button
                            variant={statusFilter === 'all' ? "default" : "outline"}
                            onClick={() => setStatusFilter('all')}
                            size="sm"
                        >
                            Alle
                        </Button>
                        <Button
                            variant={statusFilter === 'passed' ? "default" : "outline"}
                            onClick={() => setStatusFilter('passed')}
                            size="sm"
                            className={statusFilter === 'passed' ? "bg-emerald-600 hover:bg-emerald-700" : ""}
                        >
                            Nur Passed
                        </Button>
                        <Button
                            variant={statusFilter === 'rejected' ? "default" : "outline"}
                            onClick={() => setStatusFilter('rejected')}
                            size="sm"
                            className={statusFilter === 'rejected' ? "bg-red-600 hover:bg-red-700" : ""}
                        >
                            Nur Rejected
                        </Button>
                    </div>
                </div>

                {/* Table */}
                <Card>
                    <CardContent className="p-0">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead className="w-[140px]">Status</TableHead>
                                    <TableHead>Titel</TableHead>
                                    <TableHead>Preis</TableHead>
                                    <TableHead>Grund / Reason</TableHead>
                                    <TableHead className="text-right">Zeit</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {filtered.map((l) => (
                                    <TableRow key={l.id} className="hover:bg-muted/50">
                                        <TableCell>{getStatusBadge(l.filter_status)}</TableCell>
                                        <TableCell className="font-medium">
                                            <a href={l.link} target="_blank" className="hover:underline flex flex-col">
                                                <span>{l.title}</span>
                                                <span className="text-xs text-muted-foreground font-normal">{l.category}</span>
                                            </a>
                                        </TableCell>
                                        <TableCell>{l.price}</TableCell>
                                        <TableCell className="max-w-[300px]">
                                            <code className="text-xs bg-muted px-1 py-0.5 rounded">{l.filter_reason || '-'}</code>
                                        </TableCell>
                                        <TableCell className="text-right text-muted-foreground text-xs whitespace-nowrap">
                                            {new Date(l.created_at).toLocaleTimeString()}
                                        </TableCell>
                                    </TableRow>
                                ))}
                                {filtered.length === 0 && (
                                    <TableRow>
                                        <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                                            Keine Einträge für diesen Filter.
                                        </TableCell>
                                    </TableRow>
                                )}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </main>
        </div>
    )
}
