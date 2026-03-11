import { cn } from '@/lib/utils'

interface CardProps {
  title?: string
  children: React.ReactNode
  className?: string
  headerRight?: React.ReactNode
  noPadding?: boolean
}

export default function Card({
  title,
  children,
  className,
  headerRight,
  noPadding = false,
}: CardProps) {
  return (
    <div
      className={cn(
        'bg-gray-900 border border-gray-800 rounded-xl',
        className
      )}
    >
      {title && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
          <h3 className="text-sm font-semibold text-gray-200 tracking-wide">
            {title}
          </h3>
          {headerRight && (
            <div className="flex items-center gap-2">{headerRight}</div>
          )}
        </div>
      )}
      <div className={cn(!noPadding && 'p-4')}>{children}</div>
    </div>
  )
}
