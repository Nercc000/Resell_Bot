"use client"

import { useEffect, useState } from "react"
import { supabase } from "@/lib/supabase"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Plus, Trash2, Pencil } from "lucide-react"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"

type PromptTemplate = {
    id: string
    name: string
    content: string
    is_active: boolean
    created_at: string
}

export function PromptTemplatesTab() {
    // ... (state omitted for brevity, logic remains same)
    const [templates, setTemplates] = useState<PromptTemplate[]>([])
    const [newName, setNewName] = useState("")
    const [newContent, setNewContent] = useState("")
    const [loading, setLoading] = useState(true)

    // Edit State
    const [editingTemplate, setEditingTemplate] = useState<PromptTemplate | null>(null)
    const [editName, setEditName] = useState("")
    const [editContent, setEditContent] = useState("")
    const [isDialogOpen, setIsDialogOpen] = useState(false)

    useEffect(() => {
        fetchTemplates()
    }, [])

    const fetchTemplates = async () => {
        setLoading(true)
        try {
            const { data, error } = await supabase
                .from('prompt_templates')
                .select('*')
                .order('created_at', { ascending: false })

            if (error) throw error
            setTemplates(data || [])
        } catch (e) {
            console.error(e)
        } finally {
            setLoading(false)
        }
    }

    const addTemplate = async () => {
        if (!newName.trim() || !newContent.trim()) return

        const { data, error } = await supabase
            .from('prompt_templates')
            .insert([{ name: newName, content: newContent }])
            .select()

        if (data) {
            setTemplates([data[0], ...templates])
            setNewName("")
            setNewContent("")
        }
        if (error) console.error("Error adding template:", error)
    }

    const deleteTemplate = async (id: string) => {
        const { error } = await supabase
            .from('prompt_templates')
            .delete()
            .eq('id', id)

        if (!error) {
            setTemplates(templates.filter(t => t.id !== id))
        } else {
            console.error("Error deleting template:", error)
        }
    }

    const openEditDialog = (template: PromptTemplate) => {
        setEditingTemplate(template)
        setEditName(template.name)
        setEditContent(template.content)
        setIsDialogOpen(true)
    }

    const saveEdit = async () => {
        if (!editingTemplate || !editName.trim() || !editContent.trim()) return

        const { error } = await supabase
            .from('prompt_templates')
            .update({ name: editName, content: editContent })
            .eq('id', editingTemplate.id)

        if (!error) {
            setTemplates(templates.map(t => t.id === editingTemplate.id ? { ...t, name: editName, content: editContent } : t))
            setIsDialogOpen(false)
            setEditingTemplate(null)
        } else {
            console.error("Error updating template:", error)
        }
    }

    return (
        <div className="space-y-6">
            <div className="grid gap-6">
                <Card>
                    <CardHeader>
                        <CardTitle>Neuen Prompt erstellen</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-2">
                            <Label htmlFor="name">Name (z.B. &quot;Standard PS5&quot;)</Label>
                            <Input
                                id="name"
                                placeholder="Name des Templates..."
                                value={newName}
                                onChange={(e) => setNewName(e.target.value)}
                            />
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="content">Prompt Inhalt (Nutze {'{{LISTINGS}}'} als Platzhalter)</Label>
                            <Textarea
                                id="content"
                                placeholder="Du bist ein strenger Einkaufs-Bot..."
                                value={newContent}
                                onChange={(e) => setNewContent(e.target.value)}
                                className="min-h-[150px]"
                            />
                        </div>
                        <div className="flex justify-end">
                            <Button onClick={addTemplate}>
                                <Plus className="mr-2 h-4 w-4" /> Template Speichern
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Deine Prompts ({templates.length})</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead className="w-[200px]">Name</TableHead>
                                    <TableHead>Vorschau</TableHead>
                                    <TableHead className="text-right">Aktionen</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {templates.map((template) => (
                                    <TableRow key={template.id}>
                                        <TableCell className="font-medium">
                                            {template.name}
                                        </TableCell>
                                        <TableCell className="text-muted-foreground truncate max-w-[300px]">
                                            {template.content.substring(0, 80)}...
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
                                            Keine Prompts vorhanden.
                                        </TableCell>
                                    </TableRow>
                                )}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </div>

            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                <DialogContent className="sm:max-w-[625px]">
                    <DialogHeader>
                        <DialogTitle>Prompt bearbeiten</DialogTitle>
                        <DialogDescription>
                            Ändere die Anweisungen für die KI.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                        <div className="grid gap-2">
                            <Label htmlFor="edit-name">Name</Label>
                            <Input
                                id="edit-name"
                                value={editName}
                                onChange={(e) => setEditName(e.target.value)}
                            />
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="edit-content">Prompt Inhalt</Label>
                            <Textarea
                                id="edit-content"
                                value={editContent}
                                onChange={(e) => setEditContent(e.target.value)}
                                className="min-h-[300px]"
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button type="submit" onClick={saveEdit}>Änderungen Speichern</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    )
}
