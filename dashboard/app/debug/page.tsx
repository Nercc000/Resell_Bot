"use client"

import { useEffect, useState } from "react"
import { supabase } from "@/lib/supabase"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ArrowLeft, Search, Filter, ShieldCheck, ShieldAlert, RefreshCw } from "lucide-react"
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
}

export default function DebugPage() {
    const [listings, setListings] = useState<DebugListing[]>([])
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState("")
    const [statusFilter, setStatusFilter] = useState<'all' | 'passed' | 'rejected'>('all')

    const fetchListings = async () => {
        setLoading(true)
        const { data, error } = await supabase
            .from('listings')
            .select('id, title, price, link, filter_status, filter_reason, created_at, category')
            .order('created_at', { ascending: false })
            .limit(200)

        if (error) console.error(error)
        else setListings(data as DebugListing[])
        setLoading(false)
    }

    useEffect(() => {
        fetchListings()
    }, [])

    const getStatusBadge = (status: string | null) => {
        if (!status) return <Badge variant="outline" className="text-muted-foreground">Unbekannt</Badge>

        if (status.includes('passed')) {
            return <Badge className="bg-emerald-500/15 text-emerald-500 border-emerald-500/20 hover:bg-emerald-500/25"><ShieldCheck className="w-3 h-3 mr-1" /> Passed</Badge>
        }
        if (status.includes('rejected')) {
            return <Badge variant="destructive" className="bg-red-500/15 text-red-500 border-red-500/20 hover:bg-red-500/25"><ShieldAlert className="w-3 h-3 mr-1" /> Rejected</Badge>
        }
        return <Badge variant="secondary">{status}</Badge>
    }

    const filtered = listings.filter(l => {
        const matchesSearch = l.title.toLowerCase().includes(search.toLowerCase()) ||
            (l.filter_reason && l.filter_reason.toLowerCase().includes(search.toLowerCase()))

        if (statusFilter === 'passed') return matchesSearch && l.filter_status?.includes('passed')
        if (statusFilter === 'rejected') return matchesSearch && l.filter_status?.includes('rejected')
        return matchesSearch
    })

    return (
        <div className="flex min-h-screen flex-col bg-background">
            <header className="border-b sticky top-0 bg-background/95 backdrop-blur z-50">
                <div className="flex h-16 items-center px-4 md:px-6 justify-between">
                    <div className="flex items-center">
                        <Link href="/">
                            <Button variant="ghost" size="sm" className="gap-2">
                                <ArrowLeft className="h-4 w-4" />
                                Dashboard
                            </Button>
                        </Link>
                        <h1 className="ml-4 text-lg font-bold flex items-center gap-2">
                            <Filter className="w-5 h-5 text-purple-500" />
                            Filter Debugger
                        </h1>
                    </div>
                    <Button variant="outline" size="sm" onClick={fetchListings} disabled={loading}>
                        <RefreshCw className={cn("w-4 h-4 mr-2", loading && "animate-spin")} />
                        Refresh
                    </Button>
                </div>
            </header>

            <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">

                {/* Stats Cards */}
                <div className="grid gap-4 md:grid-cols-3">
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Scanned Total</CardTitle>
                            <Search className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{listings.length}</div>
                            <p className="text-xs text-muted-foreground">Letzte 200 Einträge</p>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Passed (Grün)</CardTitle>
                            <ShieldCheck className="h-4 w-4 text-emerald-500" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-emerald-500">
                                {listings.filter(l => l.filter_status?.includes('passed')).length}
                            </div>
                            <p className="text-xs text-muted-foreground">Erfolgreich gefiltert</p>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Rejected (Rot)</CardTitle>
                            <ShieldAlert className="h-4 w-4 text-red-500" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-red-500">
                                {listings.filter(l => l.filter_status?.includes('rejected')).length}
                            </div>
                            <p className="text-xs text-muted-foreground">Aussortiert durch KI/Keywords</p>
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
                                    <TableHead className="w-[100px]">Status</TableHead>
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
                                            Keine Einträge gefunden.
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
