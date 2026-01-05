"use client"

import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

export type Listing = {
    id: string
    title: string
    price: string
    link: string
    location: string | null
    created_at: string
    message_sent: boolean
    deleted: boolean
    category: 'normal' | 'abholung' | 'defekt' | null
    data?: any
}

type RealtimeContextType = {
    listings: Listing[]
    stats: {
        total: number
        sent: number
        deleted: number
        open: number
    }
}

const RealtimeContext = createContext<RealtimeContextType>({
    listings: [],
    stats: { total: 0, sent: 0, deleted: 0, open: 0 }
})

export function RealtimeProvider({ children }: { children: React.ReactNode }) {
    const [listings, setListings] = useState<Listing[]>([])

    useEffect(() => {
        // Initial fetch
        const fetchListings = async () => {
            const { data } = await supabase
                .from('listings')
                .select('*')
                .order('created_at', { ascending: false })
                .limit(100)

            if (data) setListings(data)
        }

        fetchListings()

        // Realtime subscription
        const channel = supabase
            .channel('dashboard-listings')
            .on('postgres_changes', { event: '*', schema: 'public', table: 'listings' }, (payload) => {
                if (payload.eventType === 'INSERT') {
                    setListings(prev => [payload.new as Listing, ...prev])
                } else if (payload.eventType === 'UPDATE') {
                    setListings(prev => prev.map(l => l.id === (payload.new as Listing).id ? payload.new as Listing : l))
                } else if (payload.eventType === 'DELETE') {
                    // Optional: Handle delete if rows are actually deleted
                    setListings(prev => prev.filter(l => l.id !== (payload.old as Listing).id))
                }
            })
            .subscribe()

        return () => {
            supabase.removeChannel(channel)
        }
    }, [])

    const stats = {
        total: listings.length,
        sent: listings.filter(l => l.message_sent).length,
        deleted: listings.filter(l => l.deleted).length,
        open: listings.filter(l => !l.message_sent && !l.deleted).length
    }

    return (
        <RealtimeContext.Provider value={{ listings, stats }}>
            {children}
        </RealtimeContext.Provider>
    )
}

export const useRealtime = () => useContext(RealtimeContext)
