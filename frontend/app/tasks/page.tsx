'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchTasks } from '@/lib/api'
import TaskTable from '@/components/tasks/TaskTable'
import Card from '@/components/ui/Card'
import { ListTodo, RefreshCw, ChevronLeft, ChevronRight } from 'lucide-react'

const PAGE_SIZE = 50

export default function TasksPage() {
  const [page, setPage] = useState(0)

  const {
    data,
    isLoading,
    isError,
    refetch,
    dataUpdatedAt,
  } = useQuery({
    queryKey: ['tasks', 'all', page],
    queryFn: () =>
      fetchTasks({ limit: PAGE_SIZE, offset: page * PAGE_SIZE }),
    refetchInterval: 15_000,
  })

  const tasks = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <ListTodo size={20} className="text-blue-400" />
            <h1 className="text-xl font-bold text-gray-100">Tasks</h1>
          </div>
          <p className="text-sm text-gray-500">
            {isLoading ? (
              'Loading...'
            ) : (
              <>
                <span className="text-gray-300 font-medium">{total}</span> total
                tasks
              </>
            )}
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

      {/* Error state */}
      {isError && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4">
          <p className="text-sm text-red-400">
            Failed to load tasks. Is the backend running?
          </p>
          <button
            onClick={() => refetch()}
            className="mt-2 text-xs text-red-400 hover:text-red-300 underline"
          >
            Retry
          </button>
        </div>
      )}

      {/* Task table */}
      <Card noPadding>
        <div className="p-4">
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="skeleton h-12 rounded-lg" />
              ))}
            </div>
          ) : (
            <TaskTable tasks={tasks} showFilters defaultStatus="all" />
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-800">
            <span className="text-xs text-gray-600">
              Page {page + 1} of {totalPages} · {total} tasks
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="p-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed text-gray-400 transition-all"
              >
                <ChevronLeft size={14} />
              </button>
              <div className="flex items-center gap-1">
                {[...Array(Math.min(5, totalPages))].map((_, i) => {
                  const pageNum =
                    totalPages <= 5
                      ? i
                      : Math.max(0, Math.min(totalPages - 5, page - 2)) + i
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setPage(pageNum)}
                      className={`w-7 h-7 rounded-lg text-xs font-medium transition-all ${
                        pageNum === page
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                      }`}
                    >
                      {pageNum + 1}
                    </button>
                  )
                })}
              </div>
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="p-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed text-gray-400 transition-all"
              >
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </Card>
    </div>
  )
}
