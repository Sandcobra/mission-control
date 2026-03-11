import type { CostMetrics } from '@/lib/api'
import { formatCost, formatTokens } from '@/lib/utils'
import { cn } from '@/lib/utils'

interface CostChartProps {
  metrics: CostMetrics | undefined
  loading?: boolean
}

export default function CostChart({ metrics, loading = false }: CostChartProps) {
  if (loading) {
    return (
      <div className="space-y-4">
        <div className="skeleton h-8 w-32" />
        <div className="skeleton h-40 w-full" />
        <div className="skeleton h-32 w-full" />
      </div>
    )
  }

  if (!metrics) {
    return (
      <div className="text-center py-10 text-gray-600 text-sm">
        No cost data available
      </div>
    )
  }

  const byDay = metrics.by_day ?? []
  const byAgent = metrics.by_agent ?? []

  const maxDayCost = Math.max(...byDay.map((d) => d.cost_usd), 0.0001)
  const maxAgentCost = Math.max(...byAgent.map((a) => a.cost_usd), 0.0001)

  // Last 14 days
  const recentDays = [...byDay]
    .sort((a, b) => b.date.localeCompare(a.date))
    .slice(0, 14)
    .reverse()

  const topAgents = [...byAgent]
    .sort((a, b) => b.cost_usd - a.cost_usd)
    .slice(0, 10)

  return (
    <div className="space-y-8">
      {/* Total headline */}
      <div className="flex items-end gap-4 flex-wrap">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">
            Total Spend
          </p>
          <p className="text-3xl font-bold text-gray-100">
            {formatCost(metrics.total_usd)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">
            Today
          </p>
          <p className="text-xl font-semibold text-emerald-400">
            {formatCost(metrics.today_usd)}
          </p>
        </div>
      </div>

      {/* Daily spend chart */}
      {recentDays.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
            Daily Spend (last {recentDays.length} days)
          </h4>
          {/* Bar chart */}
          <div className="flex items-end gap-1 h-24 mb-2">
            {recentDays.map((day) => {
              const heightPct = (day.cost_usd / maxDayCost) * 100
              const isToday =
                day.date === new Date().toISOString().split('T')[0]
              return (
                <div
                  key={day.date}
                  className="flex-1 flex flex-col items-center gap-1 group relative"
                  title={`${day.date}: ${formatCost(day.cost_usd)}`}
                >
                  <div className="w-full flex items-end justify-center h-20">
                    <div
                      className={cn(
                        'w-full rounded-t transition-all',
                        isToday
                          ? 'bg-emerald-500/80'
                          : 'bg-blue-600/60 group-hover:bg-blue-500/80'
                      )}
                      style={{ height: `${Math.max(2, heightPct)}%` }}
                    />
                  </div>
                  {/* Tooltip */}
                  <div className="absolute bottom-full mb-1 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-[10px] text-gray-200 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                    {day.date}
                    <br />
                    {formatCost(day.cost_usd)}
                  </div>
                </div>
              )
            })}
          </div>
          {/* X axis labels */}
          <div className="flex gap-1">
            {recentDays.map((day, i) => (
              <div key={day.date} className="flex-1 text-center">
                {(i === 0 || i === recentDays.length - 1) && (
                  <span className="text-[9px] text-gray-700 font-mono">
                    {day.date.slice(5)}
                  </span>
                )}
              </div>
            ))}
          </div>

          {/* Day table */}
          <div className="mt-4 border border-gray-800 rounded-lg overflow-hidden">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-800 bg-gray-900">
                  <th className="px-3 py-2 text-left text-gray-500 font-medium">
                    Date
                  </th>
                  <th className="px-3 py-2 text-right text-gray-500 font-medium">
                    Cost
                  </th>
                  <th className="px-3 py-2 text-right text-gray-500 font-medium">
                    Tokens In
                  </th>
                  <th className="px-3 py-2 text-right text-gray-500 font-medium">
                    Tokens Out
                  </th>
                  <th className="px-3 py-2 text-right text-gray-500 font-medium">
                    Tasks
                  </th>
                </tr>
              </thead>
              <tbody>
                {[...recentDays].reverse().map((day) => {
                  const isToday =
                    day.date === new Date().toISOString().split('T')[0]
                  return (
                    <tr
                      key={day.date}
                      className={cn(
                        'border-b border-gray-800/50',
                        isToday ? 'bg-emerald-500/5' : 'hover:bg-gray-800/30'
                      )}
                    >
                      <td className="px-3 py-2 font-mono text-gray-300">
                        {day.date}
                        {isToday && (
                          <span className="ml-2 text-[10px] text-emerald-400 font-medium">
                            today
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-gray-200 font-medium">
                        {formatCost(day.cost_usd)}
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-gray-500">
                        {formatTokens(day.input_tokens)}
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-gray-500">
                        {formatTokens(day.output_tokens)}
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-gray-500">
                        {day.task_count}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* By agent */}
      {topAgents.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
            Top Agents by Cost
          </h4>
          <div className="space-y-2">
            {topAgents.map((agent) => {
              const barWidth = (agent.cost_usd / maxAgentCost) * 100
              return (
                <div key={agent.agent_id}>
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-xs text-gray-300 font-mono truncate max-w-[180px]">
                        {agent.agent_name}
                      </span>
                      <span className="text-[10px] text-gray-600 font-mono truncate">
                        {agent.agent_key}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 shrink-0 ml-4">
                      <span className="text-[10px] text-gray-600 font-mono">
                        {formatTokens(
                          agent.input_tokens + agent.output_tokens
                        )}{' '}
                        tok
                      </span>
                      <span className="text-xs text-gray-200 font-mono font-medium w-16 text-right">
                        {formatCost(agent.cost_usd)}
                      </span>
                    </div>
                  </div>
                  <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500/70 rounded-full transition-all duration-500"
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
