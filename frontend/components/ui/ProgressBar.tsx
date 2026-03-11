import { cn } from '@/lib/utils'

interface ProgressBarProps {
  percent: number
  label?: string
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple'
  size?: 'sm' | 'md' | 'lg'
  showPercent?: boolean
  className?: string
  animated?: boolean
}

const colorMap: Record<string, string> = {
  blue: 'bg-blue-500',
  green: 'bg-green-500',
  yellow: 'bg-yellow-500',
  red: 'bg-red-500',
  purple: 'bg-purple-500',
}

const sizeMap: Record<string, string> = {
  sm: 'h-1',
  md: 'h-1.5',
  lg: 'h-2',
}

export default function ProgressBar({
  percent,
  label,
  color = 'blue',
  size = 'sm',
  showPercent = false,
  className,
  animated = false,
}: ProgressBarProps) {
  const clampedPercent = Math.min(100, Math.max(0, percent))

  return (
    <div className={cn('w-full', className)}>
      {(label || showPercent) && (
        <div className="flex justify-between items-center mb-1">
          {label && (
            <span className="text-xs text-gray-500 truncate">{label}</span>
          )}
          {showPercent && (
            <span className="text-xs text-gray-400 font-mono ml-auto">
              {Math.round(clampedPercent)}%
            </span>
          )}
        </div>
      )}
      <div
        className={cn(
          'w-full bg-gray-800 rounded-full overflow-hidden',
          sizeMap[size]
        )}
      >
        <div
          className={cn(
            'h-full rounded-full transition-all duration-500 ease-out',
            colorMap[color],
            animated && 'animate-pulse'
          )}
          style={{ width: `${clampedPercent}%` }}
        />
      </div>
    </div>
  )
}
