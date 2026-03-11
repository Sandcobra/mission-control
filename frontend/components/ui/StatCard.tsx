import { cn } from '@/lib/utils'
import type { LucideIcon } from 'lucide-react'

interface StatCardProps {
  icon: LucideIcon
  label: string
  value: string | number
  change?: {
    value: string
    positive?: boolean
  }
  iconColor?: string
  className?: string
  loading?: boolean
}

export default function StatCard({
  icon: Icon,
  label,
  value,
  change,
  iconColor = 'text-blue-400',
  className,
  loading = false,
}: StatCardProps) {
  return (
    <div
      className={cn(
        'bg-gray-900 border border-gray-800 rounded-xl p-4 flex items-start gap-3',
        className
      )}
    >
      <div
        className={cn(
          'p-2 rounded-lg bg-gray-800 shrink-0',
          iconColor
        )}
      >
        <Icon size={18} />
      </div>

      <div className="min-w-0 flex-1">
        <p className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-1">
          {label}
        </p>

        {loading ? (
          <div className="skeleton h-7 w-20 mt-1" />
        ) : (
          <p className="text-2xl font-bold text-gray-100 leading-none">
            {value}
          </p>
        )}

        {change && !loading && (
          <p
            className={cn(
              'text-xs mt-1 font-medium',
              change.positive === true
                ? 'text-green-400'
                : change.positive === false
                ? 'text-red-400'
                : 'text-gray-500'
            )}
          >
            {change.value}
          </p>
        )}
      </div>
    </div>
  )
}
