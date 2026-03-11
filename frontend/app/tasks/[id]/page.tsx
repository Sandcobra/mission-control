'use client'

import { useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import {
  fetchTask,
  fetchTaskEvents,
  fetchTaskArtifacts,
} from '@/lib/api'
import Badge, { statusToVariant } from '@/components/ui/Badge'
import ProgressBar from '@/components/ui/ProgressBar'
import EventTimeline from '@/components/tasks/EventTimeline'
import Card from '@/components/ui/Card'
import { cn, timeAgo, formatDuration, formatCost, formatTokens, formatBytes } from '@/lib/utils'
import {
  ArrowLeft,
  Clock,
  User,
  AlertTriangle,
  CheckCircle2,
  FileText,
  Activity,
  Database,
  RefreshCw,
  Download,
} from 'lucide-react'

type TabKey = 'events' | 'artifacts' | 'metadata'

const PRIORITY_COLORS: Record<string, string> = {
  critical: 'text-red-400 font-bold',
  high: 'text-orange-400 font-semibold',
  normal: 'text-gray-400',
  low: 'text-gray-600',
}

export default function TaskDetailPage() {
  const params = useParams()
  const taskId = params.id as string
  const [activeTab, setActiveTab] = useState<TabKey>('events')

  const {
    data: task,
    isLoading: taskLoading,
    isError: taskError,
    refetch,
  } = useQuery({
    queryKey: ['task', taskId],
    queryFn: () => fetchTask(taskId),
    refetchInterval: (query) =>
      query.state.data?.status === 'running' ? 10_000 : false,
  })

  const isRunning = task?.status === 'running'

  const { data: events = [], isLoading: eventsLoading } = useQuery({
    queryKey: ['task-events', taskId],
    queryFn: () => fetchTaskEvents(taskId),
    refetchInterval: isRunning ? 5_000 : 30_000,
    enabled: !!taskId,
  })

  const { data: artifacts = [], isLoading: artifactsLoading } = useQuery({
    queryKey: ['task-artifacts', taskId],
    queryFn: () => fetchTaskArtifacts(taskId),
    enabled: !!taskId,
  })

  if (taskLoading) {
    return (
      <div className="space-y-4">
        <div className="skeleton h-8 w-64 rounded-lg" />
        <div className="skeleton h-32 rounded-xl" />
        <div className="skeleton h-96 rounded-xl" />
      </div>
    )
  }

  if (taskError || !task) {
    return (
      <div className="space-y-4">
        <Link
          href="/tasks"
          className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-300 transition-colors"
        >
          <ArrowLeft size={14} />
          Back to Tasks
        </Link>
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 text-center">
          <AlertTriangle size={32} className="text-red-400 mx-auto mb-3" />
          <p className="text-red-400 font-medium">Task not found</p>
          <p className="text-gray-600 text-sm mt-1">
            Task ID: <span className="font-mono">{taskId}</span>
          </p>
        </div>
      </div>
    )
  }

  const duration =
    task.started_at && task.completed_at
      ? formatDuration(
          (new Date(task.completed_at).getTime() -
            new Date(task.started_at).getTime()) /
            1000
        )
      : task.started_at && task.status === 'running'
      ? formatDuration(
          (Date.now() - new Date(task.started_at).getTime()) / 1000
        )
      : null

  const tabs: { key: TabKey; label: string; icon: React.ReactNode; count?: number }[] = [
    {
      key: 'events',
      label: 'Events',
      icon: <Activity size={13} />,
      count: events.length,
    },
    {
      key: 'artifacts',
      label: 'Artifacts',
      icon: <FileText size={13} />,
      count: artifacts.length,
    },
    {
      key: 'metadata',
      label: 'Metadata',
      icon: <Database size={13} />,
    },
  ]

  return (
    <div className="space-y-5 max-w-6xl">
      {/* Back button */}
      <Link
        href="/tasks"
        className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-300 transition-colors"
      >
        <ArrowLeft size={14} />
        Back to Tasks
      </Link>

      {/* Task header */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <div className="flex items-start justify-between gap-4 flex-wrap mb-4">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-3 mb-2 flex-wrap">
              <Badge variant={statusToVariant(task.status)} size="md">
                {task.status}
              </Badge>
              <span
                className={cn(
                  'text-xs font-mono font-medium',
                  PRIORITY_COLORS[task.priority]
                )}
              >
                {task.priority.toUpperCase()} priority
              </span>
            </div>
            <h1 className="text-xl font-bold text-gray-100 mb-1">
              {task.title}
            </h1>
            <p className="text-sm text-gray-600 font-mono">{task.task_key}</p>
          </div>

          <button
            onClick={() => refetch()}
            className="flex items-center gap-1.5 px-3 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-xs text-gray-400 hover:text-gray-200 transition-all shrink-0"
          >
            <RefreshCw size={12} />
            Refresh
          </button>
        </div>

        {/* Description */}
        {task.description && (
          <p className="text-sm text-gray-400 mb-4 leading-relaxed">
            {task.description}
          </p>
        )}

        {/* Progress */}
        {task.status === 'running' && (
          <div className="mb-4">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-gray-500">
                {task.current_step ?? 'In progress...'}
              </span>
              <span className="text-xs text-gray-400 font-mono">
                {task.completed_steps ?? 0}/{task.total_steps ?? '?'} steps
              </span>
            </div>
            <ProgressBar
              percent={task.progress}
              color="blue"
              size="lg"
              showPercent
              animated
            />
          </div>
        )}

        {/* Result / Error */}
        {task.result_summary && (
          <div className="mb-4 p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle2 size={13} className="text-green-400" />
              <span className="text-xs font-medium text-green-400">Result</span>
            </div>
            <p className="text-sm text-gray-300">{task.result_summary}</p>
          </div>
        )}

        {task.error_message && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle size={13} className="text-red-400" />
              <span className="text-xs font-medium text-red-400">Error</span>
            </div>
            <p className="text-sm text-red-300 font-mono">{task.error_message}</p>
          </div>
        )}

        {/* Meta row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 border-t border-gray-800">
          <div>
            <p className="text-[10px] text-gray-600 uppercase tracking-wider mb-1">
              Assigned Agent
            </p>
            <div className="flex items-center gap-1.5 text-sm">
              <User size={12} className="text-gray-600" />
              <span className="text-gray-300 font-mono truncate">
                {task.assigned_agent_name ?? (
                  <span className="text-gray-600">unassigned</span>
                )}
              </span>
            </div>
          </div>

          <div>
            <p className="text-[10px] text-gray-600 uppercase tracking-wider mb-1">
              Created
            </p>
            <div className="flex items-center gap-1.5 text-sm">
              <Clock size={12} className="text-gray-600" />
              <span className="text-gray-300 font-mono">
                {timeAgo(task.created_at)}
              </span>
            </div>
          </div>

          {task.started_at && (
            <div>
              <p className="text-[10px] text-gray-600 uppercase tracking-wider mb-1">
                Duration
              </p>
              <span className="text-sm text-gray-300 font-mono">
                {duration ?? '—'}
              </span>
            </div>
          )}

          {(task.cost_usd !== null || task.input_tokens !== null) && (
            <div>
              <p className="text-[10px] text-gray-600 uppercase tracking-wider mb-1">
                Cost / Tokens
              </p>
              <span className="text-sm text-gray-300 font-mono">
                {task.cost_usd !== null ? formatCost(task.cost_usd) : '—'}
                {task.input_tokens !== null && (
                  <span className="text-gray-600 text-xs ml-1">
                    {formatTokens(
                      (task.input_tokens ?? 0) + (task.output_tokens ?? 0)
                    )}{' '}
                    tok
                  </span>
                )}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div>
        <div className="flex items-center gap-1 mb-4 border-b border-gray-800">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={cn(
                'flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-all border-b-2 -mb-px',
                activeTab === tab.key
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-300'
              )}
            >
              {tab.icon}
              {tab.label}
              {tab.count !== undefined && (
                <span
                  className={cn(
                    'text-[10px] px-1.5 py-0.5 rounded-full font-mono',
                    activeTab === tab.key
                      ? 'bg-blue-500/20 text-blue-400'
                      : 'bg-gray-800 text-gray-600'
                  )}
                >
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Events tab */}
        {activeTab === 'events' && (
          <Card noPadding>
            <div className="p-4">
              {eventsLoading ? (
                <div className="space-y-3">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="skeleton h-14 rounded-lg" />
                  ))}
                </div>
              ) : (
                <EventTimeline events={events} autoScroll />
              )}
            </div>
          </Card>
        )}

        {/* Artifacts tab */}
        {activeTab === 'artifacts' && (
          <Card noPadding>
            <div className="p-4">
              {artifactsLoading ? (
                <div className="space-y-3">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="skeleton h-16 rounded-lg" />
                  ))}
                </div>
              ) : artifacts.length === 0 ? (
                <div className="text-center py-10 text-gray-600">
                  <FileText size={32} className="mx-auto mb-3 text-gray-700" />
                  <p className="text-sm">No artifacts yet</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {artifacts.map((artifact) => (
                    <div
                      key={artifact.artifact_id}
                      className="flex items-center justify-between gap-4 p-3 bg-gray-800/50 border border-gray-700/50 rounded-lg hover:bg-gray-800 transition-colors"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <FileText
                          size={18}
                          className="text-gray-500 shrink-0"
                        />
                        <div className="min-w-0">
                          <p className="text-sm text-gray-200 font-medium truncate">
                            {artifact.name}
                          </p>
                          <p className="text-xs text-gray-600 font-mono">
                            {artifact.artifact_type} · {artifact.content_type}
                            {artifact.size_bytes !== null &&
                              ` · ${formatBytes(artifact.size_bytes)}`}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <span className="text-xs text-gray-600 font-mono">
                          {timeAgo(artifact.created_at)}
                        </span>
                        {artifact.url && (
                          <a
                            href={artifact.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-1.5 bg-gray-700 hover:bg-gray-600 rounded-lg text-gray-400 hover:text-gray-200 transition-all"
                          >
                            <Download size={13} />
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Card>
        )}

        {/* Metadata tab */}
        {activeTab === 'metadata' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Timestamps */}
            <Card title="Timestamps">
              <div className="space-y-3">
                {[
                  { label: 'Created', value: task.created_at },
                  { label: 'Started', value: task.started_at },
                  { label: 'Completed', value: task.completed_at },
                  { label: 'Updated', value: task.updated_at },
                ].map(({ label, value }) => (
                  <div key={label} className="flex justify-between items-center">
                    <span className="text-xs text-gray-500">{label}</span>
                    <span className="text-xs text-gray-300 font-mono">
                      {value
                        ? new Date(value).toLocaleString()
                        : <span className="text-gray-700">—</span>}
                    </span>
                  </div>
                ))}
              </div>
            </Card>

            {/* Cost & Tokens */}
            <Card title="Usage">
              <div className="space-y-3">
                {[
                  { label: 'Cost', value: task.cost_usd !== null ? formatCost(task.cost_usd) : '—' },
                  { label: 'Input Tokens', value: task.input_tokens !== null ? formatTokens(task.input_tokens) : '—' },
                  { label: 'Output Tokens', value: task.output_tokens !== null ? formatTokens(task.output_tokens ?? 0) : '—' },
                  {
                    label: 'Total Tokens',
                    value:
                      task.input_tokens !== null
                        ? formatTokens(
                            (task.input_tokens ?? 0) + (task.output_tokens ?? 0)
                          )
                        : '—',
                  },
                ].map(({ label, value }) => (
                  <div key={label} className="flex justify-between items-center">
                    <span className="text-xs text-gray-500">{label}</span>
                    <span className="text-xs text-gray-300 font-mono">{value}</span>
                  </div>
                ))}
              </div>
            </Card>

            {/* Input data */}
            {task.input_data && Object.keys(task.input_data).length > 0 && (
              <Card title="Input Data" className="lg:col-span-2">
                <pre className="text-xs text-gray-400 font-mono overflow-x-auto bg-gray-950 rounded-lg p-3 max-h-48">
                  {JSON.stringify(task.input_data, null, 2)}
                </pre>
              </Card>
            )}

            {/* Output data */}
            {task.output_data && Object.keys(task.output_data).length > 0 && (
              <Card title="Output Data" className="lg:col-span-2">
                <pre className="text-xs text-gray-400 font-mono overflow-x-auto bg-gray-950 rounded-lg p-3 max-h-48">
                  {JSON.stringify(task.output_data, null, 2)}
                </pre>
              </Card>
            )}

            {/* Extra metadata */}
            {task.metadata && Object.keys(task.metadata).length > 0 && (
              <Card title="Metadata" className="lg:col-span-2">
                <pre className="text-xs text-gray-400 font-mono overflow-x-auto bg-gray-950 rounded-lg p-3 max-h-48">
                  {JSON.stringify(task.metadata, null, 2)}
                </pre>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
