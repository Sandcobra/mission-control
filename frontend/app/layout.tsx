'use client'

import './globals.css'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { LiveEventsProvider } from '@/lib/liveEvents'
import LiveDot from '@/components/ui/LiveDot'
import {
  LayoutDashboard,
  Bot,
  ListTodo,
  AlertOctagon,
  DollarSign,
  Menu,
  X,
} from 'lucide-react'

const NAV_ITEMS = [
  { href: '/', label: 'Overview', icon: LayoutDashboard },
  { href: '/agents', label: 'Agents', icon: Bot },
  { href: '/tasks', label: 'Tasks', icon: ListTodo },
  { href: '/alerts', label: 'Alerts', icon: AlertOctagon },
  { href: '/costs', label: 'Costs', icon: DollarSign },
]

function Sidebar({
  pathname,
  onClose,
}: {
  pathname: string
  onClose?: () => void
}) {
  return (
    <aside className="flex flex-col h-full bg-gray-950 border-r border-gray-800">
      {/* Logo */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-gray-800">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center shrink-0">
            <span className="text-white font-bold text-sm">M</span>
          </div>
          <div>
            <p className="text-sm font-bold text-gray-100 leading-none">
              Mission Control
            </p>
            <p className="text-[10px] text-gray-600 mt-0.5">Agent Platform</p>
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-300 lg:hidden"
          >
            <X size={18} />
          </button>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const isActive =
            href === '/' ? pathname === '/' : pathname.startsWith(href)
          return (
            <Link
              key={href}
              href={href}
              onClick={onClose}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
                isActive
                  ? 'bg-blue-600/15 text-blue-400 border border-blue-600/20'
                  : 'text-gray-500 hover:text-gray-200 hover:bg-gray-800/60'
              )}
            >
              <Icon
                size={16}
                className={isActive ? 'text-blue-400' : 'text-gray-600'}
              />
              {label}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-gray-800">
        <p className="text-[10px] text-gray-700 font-mono">
          v1.0.0 · mission-control
        </p>
      </div>
    </aside>
  )
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 10_000,
            retry: 2,
            refetchOnWindowFocus: false,
          },
        },
      })
  )
  const pathname = usePathname()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [dateStr, setDateStr] = useState('')
  useEffect(() => {
    setDateStr(
      new Date().toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
      })
    )
  }, [])

  const currentPage =
    NAV_ITEMS.find((item) =>
      item.href === '/' ? pathname === '/' : pathname.startsWith(item.href)
    )?.label ?? 'Overview'

  return (
    <html lang="en" className="dark">
      <head>
        <title>Mission Control</title>
        <meta name="description" content="AI Agent Mission Control Dashboard" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link
          rel="preconnect"
          href="https://fonts.googleapis.com"
        />
      </head>
      <body className="bg-gray-950 text-gray-200 min-h-screen">
        <QueryClientProvider client={queryClient}>
        <LiveEventsProvider>
          <div className="flex h-screen overflow-hidden">
            {/* Desktop sidebar */}
            <div className="hidden lg:flex lg:flex-col lg:w-52 shrink-0">
              <Sidebar pathname={pathname} />
            </div>

            {/* Mobile sidebar overlay */}
            {mobileOpen && (
              <div className="lg:hidden fixed inset-0 z-50 flex">
                <div
                  className="fixed inset-0 bg-black/60 backdrop-blur-sm"
                  onClick={() => setMobileOpen(false)}
                />
                <div className="relative w-52 shrink-0 z-10">
                  <Sidebar
                    pathname={pathname}
                    onClose={() => setMobileOpen(false)}
                  />
                </div>
              </div>
            )}

            {/* Main content area */}
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
              {/* Top bar */}
              <header className="flex items-center gap-3 px-4 py-3 bg-gray-950 border-b border-gray-800 shrink-0">
                <button
                  onClick={() => setMobileOpen(true)}
                  className="lg:hidden text-gray-500 hover:text-gray-200 p-1"
                >
                  <Menu size={20} />
                </button>

                <div className="flex items-center gap-2">
                  <h1 className="text-sm font-semibold text-gray-200">
                    {currentPage}
                  </h1>
                </div>

                <div className="ml-auto flex items-center gap-3">
                  <LiveDot color="green" size="sm" label="LIVE" />
                  {dateStr && (
                    <span className="text-[10px] text-gray-700 font-mono hidden sm:block">
                      {dateStr}
                    </span>
                  )}
                </div>
              </header>

              {/* Page content */}
              <main className="flex-1 overflow-y-auto">
                <div className="p-4 lg:p-6">{children}</div>
              </main>
            </div>
          </div>
        </LiveEventsProvider>
        </QueryClientProvider>
      </body>
    </html>
  )
}
