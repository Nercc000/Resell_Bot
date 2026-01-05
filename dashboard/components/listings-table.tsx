"use client"

import { useState } from "react"
import { useRealtime } from "@/components/realtime-provider"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { ExternalLink, Package, Truck, AlertTriangle, Filter } from "lucide-react"
import { supabase } from "@/lib/supabase"
import { cn } from "@/lib/utils"

type StatusFilter = 'all' | 'open' | 'sent' | 'deleted'
type CategoryFilter = 'all' | 'normal' | 'abholung' | 'defekt'

export function ListingsTable() {
    const { listings } = useRealtime()
    const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
    const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>('all')

    const timeAgo = (dateStr: string) => {
        const date = new Date(dateStr)
        const now = new Date()
        const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)

        if (diffInSeconds < 60) return 'Gerade eben'
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} min`
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} std`
        return `${Math.floor(diffInSeconds / 86400)} d`
    }

    const updateStatus = async (id: string, status: 'sent' | 'deleted' | 'open') => {
        try {
            const updates = {
                message_sent: status === 'sent',
                deleted: status === 'deleted'
            }
            await supabase.from('listings').update(updates).eq('id', id)

            if (status === 'open') {
                await supabase.from('sent_messages').delete().eq('listing_id', id)
            } else if (status === 'sent') {
                await supabase.from('sent_messages').upsert({
                    listing_id: id,
                    status: 'sent',
                    sent_at: new Date().toISOString(),
                    log: 'Manually marked as sent via Dashboard'
                }).select()
            }
        } catch (e) {
            console.error("Error updating status:", e)
        }
    }

    const updateCategory = async (id: string, category: 'normal' | 'abholung' | 'defekt') => {
        try {
            await supabase.from('listings').update({ category }).eq('id', id)
        } catch (e) {
            console.error("Error updating category:", e)
        }
    }

    // Filter listings
    const filteredListings = listings.filter(l => {
        // Status filter
        if (statusFilter === 'open' && (l.message_sent || l.deleted)) return false
        if (statusFilter === 'sent' && !l.message_sent) return false
        if (statusFilter === 'deleted' && !l.deleted) return false

        // Category filter
        const cat = l.category || 'normal'
        if (categoryFilter !== 'all' && cat !== categoryFilter) return false

        return true
    })

    // Counts for badges
    const counts = {
        all: listings.length,
        open: listings.filter(l => !l.message_sent && !l.deleted).length,
        sent: listings.filter(l => l.message_sent).length,
        deleted: listings.filter(l => l.deleted).length,
        normal: listings.filter(l => (l.category || 'normal') === 'normal').length,
        abholung: listings.filter(l => l.category === 'abholung').length,
        defekt: listings.filter(l => l.category === 'defekt').length,
    }

    const getCategoryBadge = (category: string | null) => {
        switch (category) {
            case 'abholung':
                return <Badge variant="outline" className="ml-2 bg-amber-500/10 border-amber-500/30 text-amber-400 text-[10px] px-1.5">🚗 Abholung</Badge>
            case 'defekt':
                return <Badge variant="outline" className="ml-2 bg-red-500/10 border-red-500/30 text-red-400 text-[10px] px-1.5">⚠️ Defekt</Badge>
            default:
                return null
        }
    }

    return (
        <Card className="bg-gradient-to-br from-background to-muted/20 backdrop-blur-sm border-muted/50">
            <CardHeader className="pb-3">
                <div className="flex flex-col gap-3">
                    <div className="flex items-center justify-between">
                        <CardTitle className="text-base font-semibold flex items-center gap-2">
                            <Package className="h-5 w-5 text-primary" />
                            Live Listings
                            <Badge variant="secondary" className="ml-1">{filteredListings.length}</Badge>
                        </CardTitle>
                    </div>

                    {/* Status Filter Pills */}
                    <div className="flex gap-1.5 flex-wrap">
                        <span className="text-xs text-muted-foreground mr-1 flex items-center"><Filter className="h-3 w-3 mr-1" />Status:</span>
                        {(['all', 'open', 'sent', 'deleted'] as const).map((s) => (
                            <button
                                key={s}
                                onClick={() => setStatusFilter(s)}
                                className={cn(
                                    "px-2 py-0.5 rounded-full text-xs font-medium transition-all",
                                    statusFilter === s
                                        ? "bg-primary text-primary-foreground"
                                        : "bg-muted/50 text-muted-foreground hover:bg-muted"
                                )}
                            >
                                {s === 'all' ? 'Alle' : s === 'open' ? 'Offen' : s === 'sent' ? 'Gesendet' : 'Gelöscht'}
                                <span className="ml-1 opacity-70">({counts[s]})</span>
                            </button>
                        ))}
                    </div>

                    {/* Category Filter Pills */}
                    <div className="flex gap-1.5 flex-wrap">
                        <span className="text-xs text-muted-foreground mr-1 flex items-center"><Truck className="h-3 w-3 mr-1" />Kategorie:</span>
                        {(['all', 'normal', 'abholung', 'defekt'] as const).map((c) => (
                            <button
                                key={c}
                                onClick={() => setCategoryFilter(c)}
                                className={cn(
                                    "px-2 py-0.5 rounded-full text-xs font-medium transition-all",
                                    categoryFilter === c
                                        ? c === 'abholung' ? "bg-amber-500 text-white"
                                            : c === 'defekt' ? "bg-red-500 text-white"
                                                : "bg-primary text-primary-foreground"
                                        : "bg-muted/50 text-muted-foreground hover:bg-muted"
                                )}
                            >
                                {c === 'all' ? 'Alle' : c === 'normal' ? '📦 Normal' : c === 'abholung' ? '🚗 Abholung' : '⚠️ Defekt'}
                                <span className="ml-1 opacity-70">({counts[c]})</span>
                            </button>
                        ))}
                    </div>
                </div>
            </CardHeader>
            <CardContent className="pt-0">
                <ScrollArea className="h-[500px] rounded-lg border border-muted/50 bg-black/10">
                    <Table>
                        <TableHeader>
                            <TableRow className="hover:bg-transparent">
                                <TableHead className="w-[100px]">Status</TableHead>
                                <TableHead>Titel</TableHead>
                                <TableHead className="w-[100px]">Preis</TableHead>
                                <TableHead className="text-right w-[80px]">Zeit</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {filteredListings.map((listing) => (
                                <TableRow key={listing.id} className="group">
                                    <TableCell>
                                        <DropdownMenu>
                                            <DropdownMenuTrigger asChild>
                                                <button className="outline-none">
                                                    {listing.deleted ? (
                                                        <Badge variant="destructive" className="cursor-pointer hover:opacity-80 text-xs">Gelöscht ▾</Badge>
                                                    ) : listing.message_sent ? (
                                                        <Badge className="bg-emerald-600 hover:bg-emerald-700 cursor-pointer text-xs">Gesendet ▾</Badge>
                                                    ) : (
                                                        <Badge variant="secondary" className="cursor-pointer hover:bg-secondary/80 text-xs">Offen ▾</Badge>
                                                    )}
                                                </button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent align="start">
                                                <DropdownMenuLabel>Status</DropdownMenuLabel>
                                                <DropdownMenuItem onClick={() => updateStatus(listing.id, 'sent')}>
                                                    ✅ Als Gesendet
                                                </DropdownMenuItem>
                                                <DropdownMenuItem onClick={() => updateStatus(listing.id, 'deleted')}>
                                                    ❌ Als Gelöscht
                                                </DropdownMenuItem>
                                                <DropdownMenuItem onClick={() => updateStatus(listing.id, 'open')}>
                                                    🔄 Als Offen (Reset)
                                                </DropdownMenuItem>
                                                <DropdownMenuSeparator />
                                                <DropdownMenuLabel>Kategorie</DropdownMenuLabel>
                                                <DropdownMenuItem onClick={() => updateCategory(listing.id, 'normal')}>
                                                    📦 Normal (Versand OK)
                                                </DropdownMenuItem>
                                                <DropdownMenuItem onClick={() => updateCategory(listing.id, 'abholung')}>
                                                    🚗 Nur Abholung
                                                </DropdownMenuItem>
                                                <DropdownMenuItem onClick={() => updateCategory(listing.id, 'defekt')}>
                                                    ⚠️ Defekt
                                                </DropdownMenuItem>
                                            </DropdownMenuContent>
                                        </DropdownMenu>
                                    </TableCell>
                                    <TableCell className="font-medium">
                                        <a href={listing.link} target="_blank" rel="noopener noreferrer" className="flex items-center hover:underline">
                                            <span className="truncate max-w-[250px]">{listing.title}</span>
                                            {getCategoryBadge(listing.category)}
                                            <ExternalLink className="ml-2 h-3 w-3 opacity-0 group-hover:opacity-50 shrink-0" />
                                        </a>
                                    </TableCell>
                                    <TableCell className="text-sm">{listing.price}</TableCell>
                                    <TableCell className="text-right text-muted-foreground text-xs">
                                        {timeAgo(listing.created_at)}
                                    </TableCell>
                                </TableRow>
                            ))}
                            {filteredListings.length === 0 && (
                                <TableRow>
                                    <TableCell colSpan={4} className="text-center py-8 text-muted-foreground">
                                        {listings.length === 0 ? 'Warte auf Listings...' : 'Keine Listings mit diesem Filter'}
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </ScrollArea>
            </CardContent>
        </Card>
    )
}
