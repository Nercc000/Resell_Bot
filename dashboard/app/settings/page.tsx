"use client"

import * as React from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { ArrowLeft, Save } from "lucide-react"
import Link from "next/link"

export default function SettingsPage() {
    const [loading, setLoading] = React.useState(false)
    const [config, setConfig] = React.useState<Record<string, string>>({})

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || ''

    React.useEffect(() => {
        fetch(`${apiUrl}/api/config`)
            .then(res => res.json())
            .then(data => setConfig(data))
            .catch(console.error)
    }, [])

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
            alert("Settings saved!")
        } catch (e) {
            alert("Error saving settings")
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="flex min-h-screen flex-col">
            <header className="border-b">
                <div className="flex h-16 items-center px-4 md:px-6">
                    <Link href="/">
                        <Button variant="ghost" size="icon" className="mr-2">
                            <ArrowLeft className="h-5 w-5" />
                        </Button>
                    </Link>
                    <h1 className="text-lg font-bold">Settings</h1>
                </div>
            </header>
            <main className="flex-1 space-y-6 p-8 pt-6 max-w-2xl mx-auto w-full">
                <Card>
                    <CardHeader>
                        <CardTitle>Kleinanzeigen Credentials</CardTitle>
                        <CardDescription>Login details for the bot</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="ks-email">Email</Label>
                            <Input
                                id="ks-email"
                                value={config["KLEINANZEIGEN_EMAIL"] || ""}
                                onChange={e => handleChange("KLEINANZEIGEN_EMAIL", e.target.value)}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="ks-password">Password</Label>
                            <Input
                                id="ks-password"
                                type="password"
                                value={config["KLEINANZEIGEN_PASSWORD"] || ""}
                                onChange={e => handleChange("KLEINANZEIGEN_PASSWORD", e.target.value)}
                            />
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>AI Configuration</CardTitle>
                        <CardDescription>Settings for Groq AI filtering</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="groq-key">Groq API Key</Label>
                            <Input
                                id="groq-key"
                                type="password"
                                value={config["GROQ_API_KEY"] || ""}
                                onChange={e => handleChange("GROQ_API_KEY", e.target.value)}
                            />
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Search Parameters</CardTitle>
                        <CardDescription>Location and distance settings</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="location">Home Location</Label>
                                <Input
                                    id="location"
                                    value={config["HOME_LOCATION"] || ""}
                                    onChange={e => handleChange("HOME_LOCATION", e.target.value)}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="distance">Max Distance (km)</Label>
                                <Input
                                    id="distance"
                                    type="number"
                                    value={config["MAX_PICKUP_DISTANCE_KM"] || ""}
                                    onChange={e => handleChange("MAX_PICKUP_DISTANCE_KM", e.target.value)}
                                />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Send Configuration</CardTitle>
                        <CardDescription>Control which categories the bot should message</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="flex items-center justify-between space-x-2">
                            <Label htmlFor="send-abholung" className="flex flex-col space-y-1">
                                <span>Send to "Abholung Only"</span>
                                <span className="font-normal text-sm text-muted-foreground">
                                    Send messages even if shipping is not available
                                </span>
                            </Label>
                            <Switch
                                id="send-abholung"
                                checked={config["SEND_ABHOLUNG"] === "true"}
                                onCheckedChange={(c) => handleChange("SEND_ABHOLUNG", String(c))}
                            />
                        </div>
                        <div className="flex items-center justify-between space-x-2">
                            <Label htmlFor="send-defekt" className="flex flex-col space-y-1">
                                <span>Send to "Defekt"</span>
                                <span className="font-normal text-sm text-muted-foreground">
                                    Send messages to defective items
                                </span>
                            </Label>
                            <Switch
                                id="send-defekt"
                                checked={config["SEND_DEFEKT"] === "true"}
                                onCheckedChange={(c) => handleChange("SEND_DEFEKT", String(c))}
                            />
                        </div>
                    </CardContent>
                </Card>

                <div className="flex justify-end">
                    <Button size="lg" onClick={handleSave} disabled={loading}>
                        <Save className="mr-2 h-4 w-4" />
                        {loading ? "Saving..." : "Save Changes"}
                    </Button>
                </div>
            </main>
        </div>
    )
}
