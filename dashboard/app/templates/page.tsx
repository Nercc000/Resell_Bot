"use client"

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { MessageSquare, Sparkles } from "lucide-react"
import { MessageTemplatesTab } from "@/components/templates/message-templates-tab"
import { PromptTemplatesTab } from "@/components/templates/prompt-templates-tab"

export default function TemplatesPage() {
    return (
        <div className="flex min-h-screen flex-col bg-background">
            <main className="flex-1 p-8 pt-6 max-w-4xl mx-auto w-full space-y-6">

                <div className="flex justify-between items-center mb-6">
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        Vorlagen Verwaltung
                    </h1>
                </div>

                <Tabs defaultValue="messages" className="w-full">
                    <TabsList className="grid w-full grid-cols-2 mb-8">
                        <TabsTrigger value="messages" className="flex items-center gap-2">
                            <MessageSquare className="w-4 h-4" />
                            Nachrichten Vorlagen
                        </TabsTrigger>
                        <TabsTrigger value="prompts" className="flex items-center gap-2">
                            <Sparkles className="w-4 h-4" />
                            AI Prompt Templates
                        </TabsTrigger>
                    </TabsList>

                    <TabsContent value="messages">
                        <MessageTemplatesTab />
                    </TabsContent>

                    <TabsContent value="prompts">
                        <PromptTemplatesTab />
                    </TabsContent>
                </Tabs>

            </main>
        </div>
    )
}
