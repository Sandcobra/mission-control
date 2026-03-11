import { cn } from '@/lib/utils'

interface LiveDotProps {
  color?: 'green' | 'blue' | 'red' | 'yellow'
  size?: 'sm' | 'md' | 'lg'
  label?: string
  className?: string
}

const colorMap = {
  green: {
    dot: 'bg-green-500',
    ring: 'bg-green-500/30',
    text: 'text-green-400',
  },
  blue: {
    dot: 'bg-blue-500',
    ring: 'bg-blue-500/30',
    text: 'text-blue-400',
  },
  red: {
    dot: 'bg-red-500',
    ring: 'bg-red-500/30',
    text: 'text-red-400',
  },
  yellow: {
    dot: 'bg-yellow-500',
    ring: 'bg-yellow-500/30',
    text: 'text-yellow-400',
  },
}

const sizeMap = {
  sm: { dot: 'w-1.5 h-1.5', ring: 'w-3 h-3' },
  md: { dot: 'w-2 h-2', ring: 'w-4 h-4' },
  lg: { dot: 'w-2.5 h-2.5', ring: 'w-5 h-5' },
}

export default function LiveDot({
  color = 'green',
  size = 'md',
  label,
  className,
}: LiveDotProps) {
  const colors = colorMap[color]
  const sizes = sizeMap[size]

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className="relative flex items-center justify-center">
        {/* Pulsing ring */}
        <span
          className={cn(
            'absolute rounded-full animate-ping opacity-50',
            colors.ring,
            sizes.ring
          )}
        />
        {/* Solid dot */}
        <span
          className={cn('relative rounded-full', colors.dot, sizes.dot)}
        />
      </div>
      {label && (
        <span
          className={cn('text-xs font-semibold tracking-wider uppercase', colors.text)}
        >
          {label}
        </span>
      )}
    </div>
  )
}
