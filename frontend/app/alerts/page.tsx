'use client'

import { useQuery } from '@tanstack/react-query'
import { fetchFailureMetrics } from '@/lib/api'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import { cn, timeAgo, formatDuration } from '@/lib/utils'
import Link from 'next/link'
import {
  AlertOctagon,
  AlertTriangle,
  WifiOff,
  Clock,
  RefreshCw,
  XCircle,
  Zap,
} from 'lucide-react'

export default function AlertsPage() {
  const {
    data: metrics,
    isLoading,
    isError,
    refetch,
    dataUpdatedAt,
  } = useQuery({
    queryKey: ['failure-metrics'],
    queryFn: fetchFailureMetrics,
    refetchInterval: 30_000,
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="skeleton h-8 w-32 rounded-lg" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="skeleton h-48 rounded-xl" />
          ))}
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="space-y-4">
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6">
          <p className="text-red-400 font-medium">Failed to load alert data</p>
          <button
            onClick={() => refetch()}
            className="mt-2 text-xs text-red-400 hover:text-red-300 underline"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  const recentFailures = metrics?.recent_failures ?? []
  const topErrorTypes = metrics?.top_error_types ?? []
  const staleAgents = metrics?.stale_agents ?? []
  const stuckTasks = metrics?.stuck_tasks ?? []

  const totalAlerts =
    recentFailures.length + staleAgents.length + stuckTasks.length
  const hasAlerts = totalAlerts > 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <AlertOctagon size={20} className="text-red-400" />
            <h1 className="text-xl font-bold text-gray-100">Alerts</h1>
            {hasAlerts && (
              <span className="px-2 py-0.5 bg-red-500/20 text-red-400 text-xs font-bold rounded-full border border-red-500/30 animate-pulse">
                {totalAlerts}
              </span>
            )}
          </div>
          <p className="text-sm text-gray-500">
            {metrics?.failure_count_24h ?? 0} failures in the last 24 hours
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 px-3 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-xs text-gray-400 hover:text-gray-200 transition-all"
        >
          <RefreshCw size={13} />
          <span>Refresh</span>
          {dataUpdatedAt ? (
            <span className="text-gray-600">
              {new Date(dataUpdatedAt).toLocaleTimeString()}
            </span>
          ) : null}
        </button>
      </div>

      {/* All clear */}
      {!hasAlerts && (
        <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-8 text-center">
          <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
            <Zap size={22} className="text-green-400" />
          </div>
          <p className="text-green-400 font-semibold text-lg">All systems nominal</p>
          <p className="text-gray-500 text-sm mt-1">
            No active alerts or failures detected
          </p>
        </div>
      )}

      {/* Alert sections grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Recent Failures */}
        <Card
          title="Recent Failures"
          headerRight={
            recentFailures.length > 0 ? (
              <Badge variant="error" size="sm">
                {recentFailures.length}
              </Badge>
            ) : (
              <Badge variant="success" size="sm">
                clear
              </Badge>
            )
          }
        >
          {recentFailures.length === 0 ? (
            <div className="text-center py-8 text-gray-700">
              <XCircle size={24} className="mx-auto mb-2 text-gray-800" />
              <p className="text-sm">No recent failures</p>
            </div>
          ) : (
            <div className="space-y-2">
              {recentFailures.map((failure) => (
                <Link
                  key={failure.task_id}
                  href={`/tasks/${failure.task_id}`}
                  className="block p-3 bg-red-500/5 border border-red-500/20 rounded-lg hover:bg-red-500/10 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <span className="text-sm text-gray-200 font-medium truncate">
                      {failure.title}
                    </span>
                    <span className="text-xs text-gray-500 whitespace-nowrap font-mono shrink-0">
                      {timeAgo(failure.failed_at)}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-600 font-mono">
                      {failure.task_key}
                    </span>
                    {failure.agent_name && (
                      <>
                        <span className="text-gray-700">·</span>
                        <span className="text-xs text-gray-500">
                          {failure.agent_name}
                        </span>
                      </>
                    )}
                  </div>
                  {failure.error_message && (
                    <p className="text-xs text-red-400 font-mono mt-1.5 truncate">
                      {failure.error_message}
                    </p>
                  )}
                </Link>
              ))}
            </div>
          )}
        </Card>

        {/* Top Error Types */}
        <Card
          title="Error Types"
          headerRight={
            <span className="text-xs text-gray-600 font-mono">
              last 24h
            </span>
          }
        >
          {topErrorTypes.length === 0 ? (
            <div className="text-center py-8 text-gray-700">
              <AlertTriangle
                size={24}
                className="mx-auto mb-2 text-gray-800"
              />
              <p className="text-sm">No error data</p>
            </div>
          ) : (
            <div className="space-y-3">
              {topErrorTypes.map((errorType) => {
                const maxCount = topErrorTypes[0]?.count ?? 1
                const barPct = (errorType.count / maxCount) * 100
                return (
                  <div key={errorType.error_type}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-300 font-mono truncate max-w-[200px]">
                        {errorType.error_type}
                      </span>
                      <span className="text-xs text-gray-400 font-mono font-medium ml-2">
                        {errorType.count}x
                      </span>
                    </div>
                    <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-red-500/70 rounded-full transition-all"
                        style={{ width: `${barPct}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </Card>

        {/* Stale Agents */}
        <Card
          title="Stale Agents"
          headerRight={
            staleAgents.length > 0 ? (
              <Badge variant="warning" size="sm">
                {staleAgents.length}
              </Badge>
            ) : (
              <Badge variant="success" size="sm">
                all active
              </Badge>
            )
          }
        >
          {staleAgents.length === 0 ? (
            <div className="text-center py-8 text-gray-700">
              <WifiOff size={24} className="mx-auto mb-2 text-gray-800" />
              <p className="text-sm">No stale agents</p>
            </div>
          ) : (
            <div className="space-y-2">
              {staleAgents.map((agent) => (
                <div
                  key={agent.agent_id}
                  className="flex items-center justify-between p-3 bg-yellow-500/5 border border-yellow-500/20 rounded-lg"
                >
                  <div className="min-w-0">
                    <p className="text-sm text-gray-200 font-medium truncate">
                      {agent.name}
                    </p>
                    <p className="text-xs text-gray-600 font-mono">
                      {agent.agent_key}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1 shrink-0 ml-3">
                    <Badge variant="warning" size="sm">
                      {agent.status}
                    </Badge>
                    <span className="text-[10px] text-gray-500 font-mono">
                      {timeAgo(agent.last_heartbeat)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Stuck Tasks */}
        <Card
          title="Stuck Tasks"
          headerRight={
            stuckTasks.length > 0 ? (
              <Badge variant="error" size="sm">
                {stuckTasks.length}
              </Badge>
            ) : (
              <Badge variant="success" size="sm">
                none stuck
              </Badge>
            )
          }
        >
          {stuckTasks.length === 0 ? (
            <div className="text-center py-8 text-gray-700">
              <Clock size={24} className="mx-auto mb-2 text-gray-800" />
              <p className="text-sm">No stuck tasks</p>
            </div>
          ) : (
            <div className="space-y-2">
              {stuckTasks.map((task) => (
                <Link
                  key={task.task_id}
                  href={`/tasks/${task.task_id}`}
                  className="block p-3 bg-orange-500/5 border border-orange-500/20 rounded-lg hover:bg-orange-500/10 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <span className="text-sm text-gray-200 font-medium truncate">
                      {task.title}
                    </span>
                    <Badge variant="warning" size="sm" className="shrink-0">
                      stuck
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <Clock size={10} />
                    <span>
                      Running for{' '}
                      <span
                        className={cn(
                          'font-mono font-medium',
                          task.running_for_seconds > 3600
                            ? 'text-red-400'
                            : 'text-orange-400'
                        )}
                      >
                        {formatDuration(task.running_for_seconds)}
                      </span>
                    </span>
                    {task.agent_name && (
                      <>
                        <span className="text-gray-700">·</span>
                        <span>{task.agent_name}</span>
                      </>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
