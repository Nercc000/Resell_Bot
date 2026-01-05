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
    filter_status?: string | null
    filter_reason?: string | null
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
                // Show passed or legacy items (null), hide rejected
                .or('filter_status.is.null,filter_status.ilike.%passed%')
                .order('created_at', { ascending: false })
                .limit(100)

            if (data) setListings(data)
        }

        fetchListings()

        // Realtime subscription
        const channel = supabase
            .channel('dashboard-listings')
            .on('postgres_changes', { event: '*', schema: 'public', table: 'listings' }, (payload) => {
                const newRecord = payload.new as Listing

                // Filter out rejected items from live updates
                // (Only allow if filter_status is missing/null OR contains 'passed')
                const isRejected = newRecord.filter_status && newRecord.filter_status.includes('rejected')

                if (payload.eventType === 'INSERT') {
                    if (!isRejected) {
                        setListings(prev => [newRecord, ...prev])
                    }
                } else if (payload.eventType === 'UPDATE') {
                    if (isRejected) {
                        // If it became rejected (e.g. manual update), remove it
                        setListings(prev => prev.filter(l => l.id !== newRecord.id))
                    } else {
                        // Update or Add if missing (unlikely but safe)
                        setListings(prev => {
                            const exists = prev.find(l => l.id === newRecord.id)
                            if (exists) return prev.map(l => l.id === newRecord.id ? newRecord : l)
                            return [newRecord, ...prev]
                        })
                    }
                } else if (payload.eventType === 'DELETE') {
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
