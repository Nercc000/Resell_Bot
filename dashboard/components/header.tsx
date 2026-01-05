"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { LayoutDashboard, MessageSquare, Settings, Activity, Zap } from "lucide-react"

export function Header() {
    const pathname = usePathname()

    const navItems = [
        { href: "/", label: "Dashboard", icon: LayoutDashboard },
        { href: "/templates", label: "Vorlagen", icon: MessageSquare },
        { href: "/debug", label: "Filter Test", icon: Activity },
        { href: "/settings", label: "Settings", icon: Settings },
    ]

    return (
        <header className="sticky top-0 z-50 w-full border-b bg-background/80 backdrop-blur-md supports-[backdrop-filter]:bg-background/60">
            <div className="container px-4 h-16 flex items-center justify-between max-w-7xl mx-auto">
                {/* Logo Area */}
                <div className="flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                        <Zap className="h-4 w-4 fill-current" />
                    </div>
                    <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent">
                        PS5 Resell Bot
                    </span>
                </div>

                {/* Navigation */}
                <nav className="flex items-center gap-1 md:gap-2">
                    {navItems.map((item) => {
                        const Icon = item.icon
                        const isActive = pathname === item.href

                        return (
                            <Link key={item.href} href={item.href}>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className={cn(
                                        "h-9 px-3 gap-2 transition-all duration-200",
                                        isActive
                                            ? "bg-secondary text-secondary-foreground shadow-sm"
                                            : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                                    )}
                                >
                                    <Icon className={cn("h-4 w-4", isActive && "text-primary")} />
                                    <span className={cn("hidden md:inline", isActive && "font-medium")}>
                                        {item.label}
                                    </span>
                                </Button>
                            </Link>
                        )
                    })}
                </nav>
            </div>
        </header>
    )
}
