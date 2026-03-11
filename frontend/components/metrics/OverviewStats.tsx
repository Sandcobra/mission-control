import type { OverviewMetrics } from '@/lib/api'
import StatCard from '@/components/ui/StatCard'
import { formatCost } from '@/lib/utils'
import {
  Bot,
  Play,
  AlertTriangle,
  XCircle,
  DollarSign,
  CheckCircle2,
} from 'lucide-react'

interface OverviewStatsProps {
  metrics: OverviewMetrics | undefined
  loading?: boolean
}

export default function OverviewStats({
  metrics,
  loading = false,
}: OverviewStatsProps) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3">
      <StatCard
        icon={Bot}
        label="Agents Online"
        value={metrics?.agents_online ?? 0}
        iconColor="text-green-400"
        loading={loading}
        change={
          metrics
            ? {
                value: `${metrics.agents_total} total`,
                positive: undefined,
              }
            : undefined
        }
      />

      <StatCard
        icon={Play}
        label="Tasks Running"
        value={metrics?.tasks_running ?? 0}
        iconColor="text-blue-400"
        loading={loading}
        change={
          metrics
            ? {
                value: `${metrics.tasks_queued} queued`,
                positive: undefined,
              }
            : undefined
        }
      />

      <StatCard
        icon={AlertTriangle}
        label="Tasks Blocked"
        value={metrics?.tasks_blocked ?? 0}
        iconColor="text-yellow-400"
        loading={loading}
        change={
          metrics
            ? {
                value: metrics.tasks_blocked > 0 ? 'needs attention' : 'all clear',
                positive: metrics.tasks_blocked === 0,
              }
            : undefined
        }
      />

      <StatCard
        icon={XCircle}
        label="Failures (24h)"
        value={metrics?.tasks_failed_24h ?? 0}
        iconColor="text-red-400"
        loading={loading}
        change={
          metrics
            ? {
                value:
                  metrics.tasks_failed_24h > 0
                    ? `${metrics.tasks_failed_total} total`
                    : 'no failures',
                positive: metrics.tasks_failed_24h === 0,
              }
            : undefined
        }
      />

      <StatCard
        icon={DollarSign}
        label="Spend Today"
        value={metrics ? formatCost(metrics.spend_today_usd) : '$0.00'}
        iconColor="text-emerald-400"
        loading={loading}
        change={
          metrics
            ? {
                value: `${formatCost(metrics.spend_total_usd)} total`,
                positive: undefined,
              }
            : undefined
        }
      />

      <StatCard
        icon={CheckCircle2}
        label="Completed Today"
        value={metrics?.tasks_completed_24h ?? 0}
        iconColor="text-teal-400"
        loading={loading}
        change={
          metrics
            ? {
                value: `${metrics.tasks_completed_total} all time`,
                positive: undefined,
              }
            : undefined
        }
      />
    </div>
  )
}
