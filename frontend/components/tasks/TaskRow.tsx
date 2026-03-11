import Link from 'next/link'
import type { Task } from '@/lib/api'
import Badge, { statusToVariant } from '@/components/ui/Badge'
import ProgressBar from '@/components/ui/ProgressBar'
import { cn, timeAgo, formatDuration } from '@/lib/utils'
import { User, Clock, AlertTriangle } from 'lucide-react'

interface TaskRowProps {
  task: Task
}

const PRIORITY_CONFIG: Record<string, { label: string; className: string }> = {
  critical: {
    label: '!!!',
    className: 'text-red-400 font-bold',
  },
  high: {
    label: '!!',
    className: 'text-orange-400 font-semibold',
  },
  normal: {
    label: '!',
    className: 'text-gray-600',
  },
  low: {
    label: '·',
    className: 'text-gray-700',
  },
}

export default function TaskRow({ task }: TaskRowProps) {
  const isRunning = task.status === 'running'
  const prio = PRIORITY_CONFIG[task.priority] ?? PRIORITY_CONFIG.normal

  const duration =
    task.started_at && task.completed_at
      ? formatDuration(
          (new Date(task.completed_at).getTime() -
            new Date(task.started_at).getTime()) /
            1000
        )
      : task.started_at && isRunning
      ? formatDuration(
          (Date.now() - new Date(task.started_at).getTime()) / 1000
        )
      : null

  return (
    <tr className="border-b border-gray-800 hover:bg-gray-800/40 transition-colors group">
      {/* Priority */}
      <td className="px-3 py-3 w-8 text-center">
        <span
          className={cn('font-mono text-sm', prio.className)}
          title={`Priority: ${task.priority}`}
        >
          {prio.label}
        </span>
      </td>

      {/* Title + key */}
      <td className="px-3 py-3">
        <Link
          href={`/tasks/${task.task_id}`}
          className="block group-hover:text-blue-400 transition-colors"
        >
          <p className="text-sm text-gray-200 font-medium truncate max-w-xs">
            {task.title}
          </p>
          <p className="text-xs text-gray-600 font-mono mt-0.5 truncate">
            {task.task_key}
          </p>
        </Link>
      </td>

      {/* Status */}
      <td className="px-3 py-3 whitespace-nowrap">
        <Badge variant={statusToVariant(task.status)} size="sm">
          {task.status}
        </Badge>
      </td>

      {/* Agent */}
      <td className="px-3 py-3 whitespace-nowrap">
        <div className="flex items-center gap-1.5 text-xs text-gray-400">
          <User size={11} className="text-gray-600 shrink-0" />
          <span className="font-mono truncate max-w-[120px]">
            {task.assigned_agent_name ?? (
              <span className="text-gray-600">unassigned</span>
            )}
          </span>
        </div>
      </td>

      {/* Progress */}
      <td className="px-3 py-3 min-w-[120px]">
        {isRunning && (
          <div>
            <ProgressBar
              percent={task.progress}
              color="blue"
              size="sm"
              animated
            />
            {task.current_step && (
              <p className="text-[10px] text-gray-600 mt-1 truncate max-w-[140px]">
                {task.current_step}
              </p>
            )}
          </div>
        )}
        {task.status === 'complete' && (
          <ProgressBar percent={100} color="green" size="sm" />
        )}
        {task.status === 'failed' && (
          <div className="flex items-center gap-1 text-xs text-red-400">
            <AlertTriangle size={10} />
            <span className="truncate max-w-[120px]">
              {task.error_message ?? 'Failed'}
            </span>
          </div>
        )}
      </td>

      {/* Time */}
      <td className="px-3 py-3 whitespace-nowrap text-right">
        <div className="flex flex-col items-end gap-0.5">
          <div className="flex items-center gap-1 text-xs text-gray-500">
            <Clock size={10} />
            <span>{timeAgo(task.created_at)}</span>
          </div>
          {duration && (
            <span className="text-[10px] text-gray-700 font-mono">
              {duration}
            </span>
          )}
        </div>
      </td>
    </tr>
  )
}
