import { cn, timeAgo } from '@/lib/utils'
import type { Agent } from '@/lib/api'
import Badge, { statusToVariant } from '@/components/ui/Badge'
import ProgressBar from '@/components/ui/ProgressBar'
import { Cpu, Server, GitBranch, Clock } from 'lucide-react'

interface AgentCardProps {
  agent: Agent
  compact?: boolean
}

export default function AgentCard({ agent, compact = false }: AgentCardProps) {
  const isRunning = agent.status === 'running'
  const isError = agent.status === 'error'
  const isBlocked = agent.status === 'blocked'

  return (
    <div
      className={cn(
        'bg-gray-900 border rounded-xl p-4 transition-all duration-200 hover:bg-gray-800/80',
        isRunning && 'border-blue-500/30 glow-blue',
        isError && 'border-red-500/30',
        isBlocked && 'border-yellow-500/30',
        !isRunning && !isError && !isBlocked && 'border-gray-800'
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span
              className={cn(
                'w-2 h-2 rounded-full shrink-0',
                isRunning && 'bg-blue-400 animate-pulse',
                isBlocked && 'bg-yellow-400',
                isError && 'bg-red-400',
                agent.status === 'idle' && 'bg-green-400',
                agent.status === 'offline' && 'bg-gray-600'
              )}
            />
            <h3 className="text-sm font-semibold text-gray-100 truncate">
              {agent.name}
            </h3>
          </div>
          <p className="text-xs text-gray-500 font-mono truncate pl-4">
            {agent.agent_key}
          </p>
        </div>
        <Badge variant={statusToVariant(agent.status)} size="sm">
          {agent.status}
        </Badge>
      </div>

      {/* Role */}
      <div className="mb-3">
        <Badge variant="neutral" size="sm">
          {agent.role}
        </Badge>
      </div>

      {/* Runtime info */}
      <div className="space-y-1.5 mb-3">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <Cpu size={11} className="shrink-0 text-gray-600" />
          <span className="truncate font-mono">{agent.runtime_type}</span>
          <span className="text-gray-700">·</span>
          <span className="truncate text-gray-400">{agent.model_name}</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <Server size={11} className="shrink-0 text-gray-600" />
          <span className="truncate font-mono">{agent.host}</span>
        </div>
        {agent.version && (
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <GitBranch size={11} className="shrink-0 text-gray-600" />
            <span className="font-mono">v{agent.version}</span>
          </div>
        )}
      </div>

      {/* Current task */}
      {agent.current_task_title && !compact && (
        <div className="mb-3 p-2 bg-gray-800/60 rounded-lg border border-gray-700/50">
          <p className="text-xs text-gray-500 mb-1">Current task</p>
          <p className="text-xs text-gray-300 truncate">{agent.current_task_title}</p>
          {agent.current_task_progress !== null && (
            <div className="mt-2">
              <ProgressBar
                percent={agent.current_task_progress}
                color="blue"
                size="sm"
                showPercent
                animated={isRunning}
              />
            </div>
          )}
        </div>
      )}

      {/* Last heartbeat */}
      <div className="flex items-center gap-1.5 text-xs text-gray-600">
        <Clock size={10} className="shrink-0" />
        <span>
          {agent.last_heartbeat
            ? timeAgo(agent.last_heartbeat)
            : 'Never'}
        </span>
      </div>
    </div>
  )
}
