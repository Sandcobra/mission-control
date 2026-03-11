'use client'

import { useQuery } from '@tanstack/react-query'
import {
  fetchOverviewMetrics,
  fetchAgents,
  fetchTasks,
} from '@/lib/api'
import OverviewStats from '@/components/metrics/OverviewStats'
import AgentGrid from '@/components/agents/AgentGrid'
import TaskTable from '@/components/tasks/TaskTable'
import LiveEventFeed from '@/components/live/LiveEventFeed'
import Card from '@/components/ui/Card'
import { RefreshCw } from 'lucide-react'

export default function OverviewPage() {
  const {
    data: metrics,
    isLoading: metricsLoading,
    dataUpdatedAt: metricsUpdatedAt,
    refetch: refetchMetrics,
  } = useQuery({
    queryKey: ['overview-metrics'],
    queryFn: fetchOverviewMetrics,
    refetchInterval: 30_000,
  })

  const { data: agentsData, isLoading: agentsLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: () => fetchAgents(),
    refetchInterval: 15_000,
  })

  const { data: tasksData, isLoading: tasksLoading } = useQuery({
    queryKey: ['tasks', 'active'],
    queryFn: () =>
      fetchTasks({ limit: 50, offset: 0 }),
    refetchInterval: 15_000,
  })

  const agents = agentsData ?? []
  const allTasks = tasksData?.items ?? []
  const activeTasks = allTasks.filter((t) =>
    ['running', 'blocked', 'queued'].includes(t.status)
  )

  return (
    <div className="space-y-6">
      {/* Overview stats */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            System Overview
          </h2>
          <button
            onClick={() => refetchMetrics()}
            className="flex items-center gap-1.5 text-xs text-gray-600 hover:text-gray-400 transition-colors"
          >
            <RefreshCw size={11} />
            <span className="hidden sm:inline">
              {metricsUpdatedAt
                ? `Updated ${new Date(metricsUpdatedAt).toLocaleTimeString()}`
                : 'Refresh'}
            </span>
          </button>
        </div>
        <OverviewStats metrics={metrics} loading={metricsLoading} />
      </div>

      {/* Main grid: Live feed + Agents */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* Live Event Feed */}
        <Card noPadding className="h-[420px] flex flex-col overflow-hidden">
          <LiveEventFeed />
        </Card>

        {/* Agent grid */}
        <Card
          title="Agents"
          headerRight={
            <span className="text-xs text-gray-600 font-mono">
              {agents.length} total
            </span>
          }
        >
          {agentsLoading ? (
            <div className="grid grid-cols-2 gap-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="skeleton h-32 rounded-xl" />
              ))}
            </div>
          ) : (
            <AgentGrid agents={agents} compact maxCount={6} />
          )}
        </Card>
      </div>

      {/* Active tasks */}
      <Card
        title="Active Tasks"
        headerRight={
          <span className="text-xs text-gray-600 font-mono">
            {activeTasks.length} active
          </span>
        }
      >
        {tasksLoading ? (
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="skeleton h-10 rounded-lg" />
            ))}
          </div>
        ) : (
          <TaskTable
            tasks={activeTasks}
            showFilters={false}
            defaultStatus="all"
          />
        )}
      </Card>
    </div>
  )
}
