'use client'

import { useQuery } from '@tanstack/react-query'
import { fetchAgents } from '@/lib/api'
import AgentGrid from '@/components/agents/AgentGrid'
import { RefreshCw, Bot } from 'lucide-react'

export default function AgentsPage() {
  const {
    data: agents,
    isLoading,
    isError,
    refetch,
    dataUpdatedAt,
  } = useQuery({
    queryKey: ['agents'],
    queryFn: () => fetchAgents(),
    refetchInterval: 15_000,
  })

  const agentList = agents ?? []
  const onlineCount = agentList.filter(
    (a) => a.status !== 'offline'
  ).length
  const runningCount = agentList.filter((a) => a.status === 'running').length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Bot size={20} className="text-blue-400" />
            <h1 className="text-xl font-bold text-gray-100">Agents</h1>
          </div>
          <p className="text-sm text-gray-500">
            {isLoading ? (
              'Loading...'
            ) : (
              <>
                <span className="text-gray-300 font-medium">{agentList.length}</span>{' '}
                total ·{' '}
                <span className="text-green-400 font-medium">{onlineCount}</span>{' '}
                online ·{' '}
                <span className="text-blue-400 font-medium">{runningCount}</span>{' '}
                running
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
            Failed to load agents. Is the backend running?
          </p>
          <button
            onClick={() => refetch()}
            className="mt-2 text-xs text-red-400 hover:text-red-300 underline"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading skeleton */}
      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="skeleton h-48 rounded-xl" />
          ))}
        </div>
      )}

      {/* Agent grid */}
      {!isLoading && !isError && (
        <>
          {agentList.length === 0 ? (
            <div className="text-center py-20">
              <Bot size={40} className="text-gray-700 mx-auto mb-3" />
              <p className="text-gray-500 text-sm">No agents registered yet</p>
              <p className="text-gray-600 text-xs mt-1">
                Agents will appear here once they connect to the platform
              </p>
            </div>
          ) : (
            <AgentGrid agents={agentList} />
          )}
        </>
      )}
    </div>
  )
}
