'use client'

import { useQuery } from '@tanstack/react-query'
import { fetchCostMetrics } from '@/lib/api'
import CostChart from '@/components/metrics/CostChart'
import Card from '@/components/ui/Card'
import { formatCost, formatTokens } from '@/lib/utils'
import { DollarSign, RefreshCw, TrendingUp } from 'lucide-react'

export default function CostsPage() {
  const {
    data: metrics,
    isLoading,
    isError,
    refetch,
    dataUpdatedAt,
  } = useQuery({
    queryKey: ['cost-metrics'],
    queryFn: fetchCostMetrics,
    refetchInterval: 60_000,
  })

  if (isError) {
    return (
      <div className="space-y-4">
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6">
          <p className="text-red-400 font-medium">Failed to load cost data</p>
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

  const byAgent = metrics?.by_agent ?? []
  const totalTokens = byAgent.reduce(
    (sum, a) => sum + a.input_tokens + a.output_tokens,
    0
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <DollarSign size={20} className="text-emerald-400" />
            <h1 className="text-xl font-bold text-gray-100">Costs</h1>
          </div>
          <p className="text-sm text-gray-500">
            LLM spend across all agents and tasks
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

      {/* Summary stats */}
      {!isLoading && metrics && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            {
              label: 'Total Spend',
              value: formatCost(metrics.total_usd),
              icon: DollarSign,
              color: 'text-emerald-400',
              bg: 'bg-emerald-500/10',
            },
            {
              label: 'Today',
              value: formatCost(metrics.today_usd),
              icon: TrendingUp,
              color: 'text-blue-400',
              bg: 'bg-blue-500/10',
            },
            {
              label: 'Total Tokens',
              value: formatTokens(totalTokens),
              icon: DollarSign,
              color: 'text-purple-400',
              bg: 'bg-purple-500/10',
            },
            {
              label: 'Active Agents',
              value: byAgent.length,
              icon: DollarSign,
              color: 'text-yellow-400',
              bg: 'bg-yellow-500/10',
            },
          ].map(({ label, value, color, bg }) => (
            <div
              key={label}
              className="bg-gray-900 border border-gray-800 rounded-xl p-4"
            >
              <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">
                {label}
              </p>
              <p
                className={`text-2xl font-bold font-mono ${color}`}
              >
                {value}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Main cost chart */}
      <Card title="Spend Overview">
        <CostChart metrics={metrics} loading={isLoading} />
      </Card>

      {/* By agent detail table */}
      {!isLoading && byAgent.length > 0 && (
        <Card title="Agent Cost Breakdown" noPadding>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-800 bg-gray-900">
                  <th className="px-4 py-3 text-left text-gray-500 font-medium uppercase tracking-wider">
                    Agent
                  </th>
                  <th className="px-4 py-3 text-right text-gray-500 font-medium uppercase tracking-wider">
                    Cost
                  </th>
                  <th className="px-4 py-3 text-right text-gray-500 font-medium uppercase tracking-wider">
                    Input Tok
                  </th>
                  <th className="px-4 py-3 text-right text-gray-500 font-medium uppercase tracking-wider">
                    Output Tok
                  </th>
                  <th className="px-4 py-3 text-right text-gray-500 font-medium uppercase tracking-wider">
                    Runs
                  </th>
                  <th className="px-4 py-3 text-right text-gray-500 font-medium uppercase tracking-wider">
                    % of Total
                  </th>
                </tr>
              </thead>
              <tbody>
                {[...byAgent]
                  .sort((a, b) => b.cost_usd - a.cost_usd)
                  .map((agent, i) => {
                    const pct =
                      metrics && metrics.total_usd > 0
                        ? (agent.cost_usd / metrics.total_usd) * 100
                        : 0
                    return (
                      <tr
                        key={agent.agent_id}
                        className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors"
                      >
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <span className="text-gray-600 font-mono w-5 text-right">
                              {i + 1}
                            </span>
                            <div>
                              <p className="text-gray-200 font-medium">
                                {agent.agent_name}
                              </p>
                              <p className="text-gray-600 font-mono text-[10px]">
                                {agent.agent_key}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-right font-mono text-emerald-400 font-medium">
                          {formatCost(agent.cost_usd)}
                        </td>
                        <td className="px-4 py-3 text-right font-mono text-gray-400">
                          {formatTokens(agent.input_tokens)}
                        </td>
                        <td className="px-4 py-3 text-right font-mono text-gray-400">
                          {formatTokens(agent.output_tokens)}
                        </td>
                        <td className="px-4 py-3 text-right font-mono text-gray-500">
                          {agent.run_count}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <div className="h-1 w-16 bg-gray-800 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-emerald-500/70 rounded-full"
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                            <span className="font-mono text-gray-500 w-8 text-right">
                              {pct.toFixed(0)}%
                            </span>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
              </tbody>
              <tfoot>
                <tr className="border-t border-gray-700 bg-gray-900/50">
                  <td className="px-4 py-3 text-gray-400 font-semibold">
                    Total
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-emerald-400 font-bold">
                    {formatCost(metrics?.total_usd ?? 0)}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-gray-400">
                    {formatTokens(byAgent.reduce((s, a) => s + a.input_tokens, 0))}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-gray-400">
                    {formatTokens(byAgent.reduce((s, a) => s + a.output_tokens, 0))}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-gray-400">
                    {byAgent.reduce((s, a) => s + a.run_count, 0)}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-gray-500">
                    100%
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </Card>
      )}

      {/* Empty state */}
      {!isLoading && byAgent.length === 0 && (
        <Card>
          <div className="text-center py-16">
            <DollarSign
              size={40}
              className="text-gray-700 mx-auto mb-3"
            />
            <p className="text-gray-500 text-sm">No cost data available</p>
            <p className="text-gray-600 text-xs mt-1">
              Cost tracking begins when agents start completing tasks
            </p>
          </div>
        </Card>
      )}
    </div>
  )
}
