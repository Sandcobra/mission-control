'use client'

import { useState } from 'react'
import type { Agent, AgentStatus } from '@/lib/api'
import AgentCard from './AgentCard'
import { cn } from '@/lib/utils'

interface AgentGridProps {
  agents: Agent[]
  compact?: boolean
  maxCount?: number
}

const STATUS_FILTERS: { label: string; value: string }[] = [
  { label: 'All', value: 'all' },
  { label: 'Running', value: 'running' },
  { label: 'Idle', value: 'idle' },
  { label: 'Blocked', value: 'blocked' },
  { label: 'Error', value: 'error' },
  { label: 'Offline', value: 'offline' },
]

export default function AgentGrid({
  agents,
  compact = false,
  maxCount,
}: AgentGridProps) {
  const [activeFilter, setActiveFilter] = useState<string>('all')

  const filtered =
    activeFilter === 'all'
      ? agents
      : agents.filter((a) => a.status === activeFilter)

  const displayed = maxCount ? filtered.slice(0, maxCount) : filtered

  const countByStatus = STATUS_FILTERS.reduce<Record<string, number>>(
    (acc, f) => {
      if (f.value === 'all') {
        acc.all = agents.length
      } else {
        acc[f.value] = agents.filter((a) => a.status === f.value).length
      }
      return acc
    },
    {}
  )

  return (
    <div>
      {/* Filter bar */}
      <div className="flex items-center gap-1 mb-4 flex-wrap">
        {STATUS_FILTERS.map((f) => {
          const count = countByStatus[f.value] ?? 0
          const isActive = activeFilter === f.value
          return (
            <button
              key={f.value}
              onClick={() => setActiveFilter(f.value)}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200'
              )}
            >
              {f.label}
              <span
                className={cn(
                  'inline-flex items-center justify-center w-4 h-4 rounded-full text-[10px] font-bold',
                  isActive ? 'bg-blue-500 text-white' : 'bg-gray-700 text-gray-400'
                )}
              >
                {count}
              </span>
            </button>
          )
        })}
      </div>

      {/* Grid */}
      {displayed.length === 0 ? (
        <div className="text-center py-12 text-gray-600">
          <p className="text-sm">No agents in this state</p>
        </div>
      ) : (
        <div
          className={cn(
            'grid gap-3',
            compact
              ? 'grid-cols-1 sm:grid-cols-2 xl:grid-cols-3'
              : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'
          )}
        >
          {displayed.map((agent) => (
            <AgentCard key={agent.agent_id} agent={agent} compact={compact} />
          ))}
        </div>
      )}

      {maxCount && filtered.length > maxCount && (
        <p className="text-xs text-gray-600 mt-3 text-center">
          +{filtered.length - maxCount} more agents
        </p>
      )}
    </div>
  )
}
