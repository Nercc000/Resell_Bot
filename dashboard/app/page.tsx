import { BotStatus } from "@/components/bot-status"
import { StatsCards } from "@/components/stats-cards"
import { LiveLogs } from "@/components/live-logs"
import { ListingsTable } from "@/components/listings-table"
import { RealtimeProvider } from "@/components/realtime-provider"
import { SearchControls } from "@/components/search-controls"
import { Button } from "@/components/ui/button"
import { Settings, MessageSquare, Filter } from "lucide-react"
import Link from "next/link"

export default function Dashboard() {
  return (
    <RealtimeProvider>
      <div className="flex min-h-screen flex-col bg-background">
        {/* Header removed - now in layout */}

        <main className="flex-1 space-y-6 p-8 pt-6">
          {/* Stats Row */}
          <StatsCards />

          {/* Main Grid */}
          <div className="grid gap-6 md:grid-cols-12">

            {/* Left Column: Controls & Logs (4 cols) */}
            <div className="md:col-span-4 space-y-6">
              <SearchControls />
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
