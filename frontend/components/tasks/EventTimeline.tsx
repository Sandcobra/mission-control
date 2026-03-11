'use client'

import { useEffect, useRef } from 'react'
import type { TaskEvent } from '@/lib/api'
import { cn, timeAgo } from '@/lib/utils'
import Badge from '@/components/ui/Badge'
import type { BadgeVariant } from '@/components/ui/Badge'

interface EventTimelineProps {
  events: TaskEvent[]
  autoScroll?: boolean
}

function eventTypeVariant(eventType: string): BadgeVariant {
  switch (eventType.toLowerCase()) {
    case 'error':
    case 'failed':
      return 'error'
    case 'complete':
    case 'completed':
    case 'success':
      return 'success'
    case 'progress':
    case 'started':
    case 'running':
      return 'info'
    case 'tool':
    case 'tool_call':
    case 'tool_result':
      return 'purple'
    case 'blocked':
    case 'warning':
      return 'warning'
    default:
      return 'neutral'
  }
}

function eventTypeColor(eventType: string): string {
  switch (eventType.toLowerCase()) {
    case 'error':
    case 'failed':
      return 'border-red-500/30 bg-red-500/5'
    case 'complete':
    case 'completed':
    case 'success':
      return 'border-green-500/30 bg-green-500/5'
    case 'progress':
    case 'started':
    case 'running':
      return 'border-blue-500/20 bg-blue-500/5'
    case 'tool':
    case 'tool_call':
    case 'tool_result':
      return 'border-purple-500/20 bg-purple-500/5'
    case 'blocked':
    case 'warning':
      return 'border-yellow-500/20 bg-yellow-500/5'
    default:
      return 'border-gray-700/50 bg-transparent'
  }
}

function dotColor(eventType: string): string {
  switch (eventType.toLowerCase()) {
    case 'error':
    case 'failed':
      return 'bg-red-500'
    case 'complete':
    case 'completed':
    case 'success':
      return 'bg-green-500'
    case 'progress':
    case 'started':
    case 'running':
      return 'bg-blue-500'
    case 'tool':
    case 'tool_call':
    case 'tool_result':
      return 'bg-purple-500'
    case 'blocked':
    case 'warning':
      return 'bg-yellow-500'
    default:
      return 'bg-gray-600'
  }
}

export default function EventTimeline({
  events,
  autoScroll = true,
}: EventTimelineProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = 0
    }
  }, [events.length, autoScroll])

  // Newest first
  const sorted = [...events].sort(
    (a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )

  if (sorted.length === 0) {
    return (
      <div className="text-center py-10 text-gray-600">
        <p className="text-sm">No events yet</p>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className="relative overflow-y-auto max-h-[600px] pr-1"
    >
      {/* Vertical line */}
      <div className="absolute left-3.5 top-0 bottom-0 w-px bg-gray-800" />

      <div className="space-y-2 relative">
        {sorted.map((event) => (
          <div
            key={event.event_id}
            className="flex gap-3 pl-3 animate-fade-in"
          >
            {/* Dot */}
            <div className="relative flex items-start pt-1 shrink-0">
              <div
                className={cn(
                  'w-2 h-2 rounded-full ring-2 ring-gray-950 shrink-0',
                  dotColor(event.event_type)
                )}
              />
            </div>

            {/* Content */}
            <div
              className={cn(
                'flex-1 min-w-0 border rounded-lg px-3 py-2 mb-1',
                eventTypeColor(event.event_type)
              )}
            >
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <span className="text-[10px] text-gray-600 font-mono whitespace-nowrap">
                  {new Date(event.created_at).toLocaleTimeString('en-US', {
                    hour12: false,
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                  })}
                </span>
                <Badge
                  variant={eventTypeVariant(event.event_type)}
                  size="sm"
                >
                  {event.event_type}
                </Badge>
                {event.agent_name && (
                  <span className="text-[10px] text-gray-500 font-mono truncate">
                    {event.agent_name}
                  </span>
                )}
                <span className="text-[10px] text-gray-700 ml-auto whitespace-nowrap">
                  {timeAgo(event.created_at)}
                </span>
              </div>
              <p className="text-xs text-gray-300 font-mono break-words leading-relaxed">
                {event.message}
              </p>
              {event.data && Object.keys(event.data).length > 0 && (
                <details className="mt-1">
                  <summary className="text-[10px] text-gray-600 cursor-pointer hover:text-gray-400">
                    data
                  </summary>
                  <pre className="text-[10px] text-gray-500 mt-1 overflow-x-auto">
                    {JSON.stringify(event.data, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
