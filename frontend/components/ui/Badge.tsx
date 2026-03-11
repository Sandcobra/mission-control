import { cn } from '@/lib/utils'

export type BadgeVariant =
  | 'success'
  | 'warning'
  | 'error'
  | 'info'
  | 'neutral'
  | 'running'
  | 'queued'
  | 'blocked'
  | 'purple'

interface BadgeProps {
  variant?: BadgeVariant
  children: React.ReactNode
  className?: string
  size?: 'sm' | 'md'
}

const variantClasses: Record<BadgeVariant, string> = {
  success: 'bg-green-500/15 text-green-400 border border-green-500/30',
  warning: 'bg-yellow-500/15 text-yellow-400 border border-yellow-500/30',
  error: 'bg-red-500/15 text-red-400 border border-red-500/30',
  info: 'bg-blue-500/15 text-blue-400 border border-blue-500/30',
  neutral: 'bg-gray-700/50 text-gray-400 border border-gray-600/30',
  running: 'bg-blue-500/15 text-blue-400 border border-blue-500/30',
  queued: 'bg-purple-500/15 text-purple-400 border border-purple-500/30',
  blocked: 'bg-yellow-500/15 text-yellow-400 border border-yellow-500/30',
  purple: 'bg-purple-500/15 text-purple-400 border border-purple-500/30',
}

export function statusToVariant(status: string): BadgeVariant {
  switch (status.toLowerCase()) {
    case 'running':
      return 'running'
    case 'complete':
    case 'completed':
    case 'success':
    case 'idle':
      return 'success'
    case 'failed':
    case 'error':
    case 'offline':
      return 'error'
    case 'blocked':
    case 'warning':
      return 'warning'
    case 'queued':
      return 'queued'
    default:
      return 'neutral'
  }
}

export default function Badge({
  variant = 'neutral',
  children,
  className,
  size = 'sm',
}: BadgeProps) {
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm'

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-md font-mono font-medium',
        sizeClasses,
        variantClasses[variant],
        className
      )}
    >
      {variant === 'running' && (
        <span className="inline-block w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
      )}
      {children}
    </span>
  )
}
