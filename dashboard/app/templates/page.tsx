"use client"

import { useEffect, useState } from "react"
import { supabase } from "@/lib/supabase"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ArrowLeft, Plus, Trash2, Pencil } from "lucide-react"
import Link from "next/link"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"

type Template = {
    id: string
    content: string
    is_active: boolean
    used_count: number
    last_used_at: string | null
}

export default function TemplatesPage() {
    const [templates, setTemplates] = useState<Template[]>([])
    const [newContent, setNewContent] = useState("")
    const [loading, setLoading] = useState(true)

    // Edit State
    const [editingTemplate, setEditingTemplate] = useState<Template | null>(null)
    const [editContent, setEditContent] = useState("")
    const [isDialogOpen, setIsDialogOpen] = useState(false)

    useEffect(() => {
        fetchTemplates()
    }, [])

    const fetchTemplates = async () => {
        setLoading(true)
        const { data, error } = await supabase
            .from('message_templates')
            .select('*')
            .order('created_at', { ascending: false })

        if (data) setTemplates(data)
        if (error) console.error("Error fetching templates:", error)
        setLoading(false)
    }

    const addTemplate = async () => {
        if (!newContent.trim()) return

        const { data, error } = await supabase
            .from('message_templates')
            .insert([{ content: newContent, is_active: true }])
            .select()

        if (data) {
            setTemplates([data[0], ...templates])
            setNewContent("")
        }
        if (error) console.error("Error adding template:", error)
    }

    const deleteTemplate = async (id: string) => {
        const { error } = await supabase
            .from('message_templates')
            .delete()
            .eq('id', id)

        if (!error) {
            setTemplates(templates.filter(t => t.id !== id))
        } else {
            console.error("Error deleting template:", error)
        }
    }

    const toggleActive = async (id: string, currentStatus: boolean) => {
        setTemplates(templates.map(t => t.id === id ? { ...t, is_active: !currentStatus } : t))
        const { error } = await supabase
            .from('message_templates')
            .update({ is_active: !currentStatus })
            .eq('id', id)
        if (error) {
            setTemplates(templates.map(t => t.id === id ? { ...t, is_active: currentStatus } : t))
            console.error(error)
        }
    }

    const openEditDialog = (template: Template) => {
        setEditingTemplate(template)
        setEditContent(template.content)
        setIsDialogOpen(true)
    }

    const saveEdit = async () => {
        if (!editingTemplate || !editContent.trim()) return

        const { error } = await supabase
            .from('message_templates')
            .update({ content: editContent })
            .eq('id', editingTemplate.id)

        if (!error) {
            setTemplates(templates.map(t => t.id === editingTemplate.id ? { ...t, content: editContent } : t))
            setIsDialogOpen(false)
            setEditingTemplate(null)
        } else {
            console.error("Error updating template:", error)
        }
    }

    return (
        <div className="flex min-h-screen flex-col bg-background">
            <header className="border-b sticky top-0 bg-background/95 backdrop-blur z-50">
                <div className="flex h-16 items-center px-4 md:px-6">
                    <Link href="/">
                        <Button variant="ghost" size="sm" className="gap-2">
                            <ArrowLeft className="h-4 w-4" />
                            Zurück zum Dashboard
                        </Button>
                    </Link>
                    <h1 className="ml-4 text-lg font-bold">Nachrichten Vorlagen</h1>
                </div>
            </header>

            <main className="flex-1 p-8 pt-6 max-w-4xl mx-auto w-full space-y-6">

                <Card>
                    <CardHeader>
                        <CardTitle>Neue Vorlage hinzufügen</CardTitle>
                    </CardHeader>
                    <CardContent className="flex gap-4">
                        <Input
                            placeholder="Nachrichtentext eingeben..."
                            value={newContent}
                            onChange={(e) => setNewContent(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && addTemplate()}
                        />
                        <Button onClick={addTemplate}>
                            <Plus className="mr-2 h-4 w-4" /> Hinzufügen
                        </Button>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Vorlagen ({templates.length})</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead className="w-[50px]">Aktiv</TableHead>
                                    <TableHead>Inhalt</TableHead>
                                    <TableHead className="text-right">Aktionen</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {templates.map((template) => (
                                    <TableRow key={template.id}>
                                        <TableCell>
                                            <Switch
                                                checked={template.is_active}
                                                onCheckedChange={() => toggleActive(template.id, template.is_active)}
                                            />
                                        </TableCell>
                                        <TableCell className="font-medium">
                                            {template.content}
                                        </TableCell>
                                        <TableCell className="text-right flex justify-end gap-2">
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                onClick={() => openEditDialog(template)}
                                            >
                                                <Pencil className="h-4 w-4" />
                                            </Button>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="text-destructive hover:text-destructive hover:bg-destructive/10"
                                                onClick={() => deleteTemplate(template.id)}
                                            >
                                                <Trash2 className="h-4 w-4" />
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                                {templates.length === 0 && !loading && (
                                    <TableRow>
                                        <TableCell colSpan={3} className="text-center py-8 text-muted-foreground">
                                            Keine Vorlagen vorhanden. Füge eine hinzu!
                                        </TableCell>
                                    </TableRow>
                                )}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>

                <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                    <DialogContent className="sm:max-w-[425px]">
                        <DialogHeader>
                            <DialogTitle>Vorlage bearbeiten</DialogTitle>
                            <DialogDescription>
                                Ändere den Text deiner Nachrichtenvorlage.
                            </DialogDescription>
                        </DialogHeader>
                        <div className="grid gap-4 py-4">
                            <div className="grid gap-2">
                                <Label htmlFor="message">Nachricht</Label>
                                <Textarea
                                    id="message"
                                    value={editContent}
                                    onChange={(e) => setEditContent(e.target.value)}
                                    className="col-span-3 min-h-[100px]"
                                />
                            </div>
                        </div>
                        <DialogFooter>
                            <Button type="submit" onClick={saveEdit}>Speichern</Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>

            </main>
        </div>
    )
}
