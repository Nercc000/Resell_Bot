"use client"

import * as React from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Search, Save, Euro } from "lucide-react"

export function SearchControls() {
    const [loading, setLoading] = React.useState(false)
    const [config, setConfig] = React.useState<Record<string, string>>({
        SEARCH_TERM: "ps5",
        MIN_PRICE: "100",
        MAX_PRICE: "350"
    })

    // Get API URL from env (frontend env var)
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || ''

    React.useEffect(() => {
        fetch(`${apiUrl}/api/config`)
            .then(res => res.json())
            .then(data => {
                // Merge with defaults
                setConfig(prev => ({ ...prev, ...data }))
            })
            .catch(console.error)
    }, [apiUrl])

    const handleChange = (key: string, value: string) => {
        setConfig(prev => ({ ...prev, [key]: value }))
    }

    const handleSave = async () => {
        setLoading(true)
        try {
            await fetch(`${apiUrl}/api/config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            })
            // Optional: Toast notification here
        } catch (e) {
            console.error("Error saving config", e)
        } finally {
            setLoading(false)
        }
    }

    return (
        <Card>
            <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2">
                    <Search className="w-5 h-5 text-primary" />
                    Such-Einstellungen
                </CardTitle>
                <CardDescription>Was soll der Bot suchen?</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="space-y-2">
                    <Label htmlFor="search-term">Suchbegriff</Label>
                    <div className="relative">
                        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                            id="search-term"
                            className="pl-9"
                            placeholder="z.B. ps5"
                            value={config.SEARCH_TERM || ""}
                            onChange={e => handleChange("SEARCH_TERM", e.target.value)}
                        />
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <Label htmlFor="min-price">Min Preis</Label>
                        <div className="relative">
                            <Euro className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input
                                id="min-price"
                                type="number"
                                className="pl-9"
                                value={config.MIN_PRICE || ""}
                                onChange={e => handleChange("MIN_PRICE", e.target.value)}
                            />
                        </div>
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="max-price">Max Preis</Label>
                        <div className="relative">
                            <Euro className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input
                                id="max-price"
                                type="number"
                                className="pl-9"
                                value={config.MAX_PRICE || ""}
                                onChange={e => handleChange("MAX_PRICE", e.target.value)}
                            />
                        </div>
                    </div>
                </div>

                <Button
                    variant="outline"
                    className="w-full"
                    onClick={handleSave}
                    disabled={loading}
                >
                    {loading ? (
                        <>Speichern...</>
                    ) : (
                        <>
                            <Save className="mr-2 h-4 w-4" />
                            Einstellungen speichern
                        </>
                    )}
                </Button>
            </CardContent>
        </Card>
    )
}
