import { BotStatus } from "@/components/bot-status"
import { StatsCards } from "@/components/stats-cards"
import { LiveLogs } from "@/components/live-logs"
import { ListingsTable } from "@/components/listings-table"
import { RealtimeProvider } from "@/components/realtime-provider"
import { Button } from "@/components/ui/button"
import { Settings, MessageSquare } from "lucide-react"
import Link from "next/link"

export default function Dashboard() {
  return (
    <RealtimeProvider>
      <div className="flex min-h-screen flex-col bg-background">
        <header className="border-b sticky top-0 bg-background/95 backdrop-blur z-50">
          <div className="flex h-16 items-center px-4 md:px-6">
            <h1 className="text-lg font-bold flex items-center gap-2">
              <span className="text-primary">🤖</span> PS5 Resell Bot
            </h1>
            <nav className="ml-auto flex items-center gap-4 sm:gap-6">
              <Link href="/templates">
                <Button variant="ghost" size="icon" title="Nachrichten Vorlagen">
                  <MessageSquare className="h-5 w-5" />
                </Button>
              </Link>
              <Link href="/settings">
                <Button variant="ghost" size="icon">
                  <Settings className="h-5 w-5" />
                  <span className="sr-only">Settings</span>
                </Button>
              </Link>
            </nav>
          </div>
        </header>

        <main className="flex-1 space-y-6 p-8 pt-6">
          {/* Stats Row */}
          <StatsCards />

          {/* Main Grid */}
          <div className="grid gap-6 md:grid-cols-12">

            {/* Left Column: Controls & Logs (4 cols) */}
            <div className="md:col-span-4 space-y-6">
              <BotStatus />
              <LiveLogs />
            </div>

            {/* Right Column: Listings Table (8 cols) */}
            <div className="md:col-span-8">
              <ListingsTable />
            </div>
          </div>
        </main>
      </div>
    </RealtimeProvider>
  )
}
