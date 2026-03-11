'use client'

import { useState } from 'react'
import type { Task } from '@/lib/api'
import TaskRow from './TaskRow'
import { cn } from '@/lib/utils'
import { Search } from 'lucide-react'

interface TaskTableProps {
  tasks: Task[]
  showFilters?: boolean
  defaultStatus?: string
}

const STATUS_FILTERS = [
  { label: 'All', value: 'all' },
  { label: 'Queued', value: 'queued' },
  { label: 'Running', value: 'running' },
  { label: 'Blocked', value: 'blocked' },
  { label: 'Failed', value: 'failed' },
  { label: 'Complete', value: 'complete' },
]

export default function TaskTable({
  tasks,
  showFilters = true,
  defaultStatus = 'all',
}: TaskTableProps) {
  const [activeFilter, setActiveFilter] = useState(defaultStatus)
  const [search, setSearch] = useState('')

  const filtered = tasks
    .filter((t) => {
      if (activeFilter !== 'all' && t.status !== activeFilter) return false
      if (
        search &&
        !t.title.toLowerCase().includes(search.toLowerCase()) &&
        !t.task_key.toLowerCase().includes(search.toLowerCase())
      )
        return false
      return true
    })
    .sort((a, b) => {
      // Sort: running first, then blocked, then queued, then rest
      const order: Record<string, number> = {
        running: 0,
        blocked: 1,
        queued: 2,
        failed: 3,
        complete: 4,
        cancelled: 5,
      }
      const oa = order[a.status] ?? 99
      const ob = order[b.status] ?? 99
      if (oa !== ob) return oa - ob
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    })

  const countByStatus = STATUS_FILTERS.reduce<Record<string, number>>(
    (acc, f) => {
      if (f.value === 'all') {
        acc.all = tasks.length
      } else {
        acc[f.value] = tasks.filter((t) => t.status === f.value).length
      }
      return acc
    },
    {}
  )

  return (
    <div>
      {showFilters && (
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 mb-4">
          {/* Status filters */}
          <div className="flex items-center gap-1 flex-wrap">
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
                      'inline-flex items-center justify-center min-w-[16px] h-4 px-1 rounded-full text-[10px] font-bold',
                      isActive
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-700 text-gray-400'
                    )}
                  >
                    {count}
                  </span>
                </button>
              )
            })}
          </div>

          {/* Search */}
          <div className="relative ml-auto">
            <Search
              size={13}
              className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-500"
            />
            <input
              type="text"
              placeholder="Search tasks..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded-lg pl-8 pr-3 py-1.5 text-xs text-gray-200 placeholder-gray-600 focus:outline-none focus:border-blue-500 w-48 transition-colors"
            />
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-800">
              <th className="px-3 py-2 w-8" />
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Task
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Agent
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Progress
              </th>
              <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Time
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-3 py-12 text-center">
                  <p className="text-sm text-gray-600">
                    {search ? 'No tasks match your search' : 'No tasks found'}
                  </p>
                </td>
              </tr>
            ) : (
              filtered.map((task) => (
                <TaskRow key={task.task_id} task={task} />
              ))
            )}
          </tbody>
        </table>
      </div>

      {filtered.length > 0 && (
        <div className="mt-3 px-3 text-xs text-gray-600">
          Showing {filtered.length} of {tasks.length} tasks
        </div>
      )}
    </div>
  )
}
