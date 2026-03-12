'use client'

import { useLiveEvents, type LiveEvent } from '@/lib/liveEvents'
import { cn } from '@/lib/utils'
import LiveDot from '@/components/ui/LiveDot'

const MAX_EVENTS = 100

function rowColor(eventType: string): string {
  const t = eventType.toLowerCase()
  if (t.includes('error') || t.includes('fail')) return 'bg-red-500/5 border-l-2 border-red-500/40'
  if (t.includes('complete') || t.includes('success')) return 'bg-green-500/5 border-l-2 border-green-500/30'
  if (t.includes('progress') || t.includes('start') || t.includes('running'))
    return 'bg-blue-500/5 border-l-2 border-blue-500/20'
  if (t.includes('tool')) return 'bg-purple-500/5 border-l-2 border-purple-500/20'
  if (t.includes('block') || t.includes('warn')) return 'bg-yellow-500/5 border-l-2 border-yellow-500/20'
  return 'border-l-2 border-transparent'
}

function eventTypeColor(eventType: string): string {
  const t = eventType.toLowerCase()
  if (t.includes('error') || t.includes('fail')) return 'text-red-400'
  if (t.includes('complete') || t.includes('success')) return 'text-green-400'
  if (t.includes('progress') || t.includes('start') || t.includes('running')) return 'text-blue-400'
  if (t.includes('tool')) return 'text-purple-400'
  if (t.includes('block') || t.includes('warn')) return 'text-yellow-400'
  return 'text-gray-500'
}

export default function LiveEventFeed() {
  const { events } = useLiveEvents()

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800 shrink-0">
        <span className="text-sm font-semibold text-gray-200">Live Events</span>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-600 font-mono">
            {events.length}/{MAX_EVENTS}
          </span>
          <LiveDot color="green" size="sm" label="LIVE" />
        </div>
      </div>

      {/* Column headers */}
      <div className="grid grid-cols-[80px_50px_100px_80px_1fr] gap-1 px-3 py-1.5 border-b border-gray-800 shrink-0">
        {['Time', 'Chan', 'Type', 'Agent', 'Message'].map((h) => (
          <span
            key={h}
            className="text-[10px] font-medium text-gray-600 uppercase tracking-wider"
          >
            {h}
          </span>
        ))}
      </div>

      {/* Events list */}
      <div className="flex-1 overflow-y-auto">
        {events.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-700 gap-2">
            <LiveDot color="green" size="md" />
            <p className="text-xs">Waiting for events...</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-800/50">
            {events.map((event) => (
              <div
                key={event.id}
                className={cn(
                  'grid grid-cols-[80px_50px_100px_80px_1fr] gap-1 px-3 py-1.5 text-[11px] font-mono hover:bg-gray-800/30 transition-colors animate-fade-in',
                  rowColor(event.event_type)
                )}
              >
                <span className="text-gray-600 tabular-nums whitespace-nowrap truncate">
                  {new Date(event.timestamp).toLocaleTimeString('en-US', {
                    hour12: false,
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                  })}
                </span>
                <span
                  className={cn(
                    'font-semibold truncate',
                    event.channel === 'task'
                      ? 'text-blue-500'
                      : 'text-purple-500'
                  )}
                >
                  {event.channel}
                </span>
                <span
                  className={cn(
                    'truncate font-medium',
                    eventTypeColor(event.event_type)
                  )}
                >
                  {event.event_type}
                </span>
                <span className="text-gray-500 truncate">
                  {event.agent_key ?? event.task_key ?? '—'}
                </span>
                <span className="text-gray-400 truncate">
                  {event.message}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
