import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.floor(seconds)}s`
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  if (hours > 0) {
    return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`
  }
  return secs > 0 ? `${minutes}m ${secs}s` : `${minutes}m`
}

export function timeAgo(timestamp: string): string {
  const now = Date.now()
  const then = new Date(timestamp).getTime()
  const diffMs = now - then
  const diffSeconds = Math.floor(diffMs / 1000)

  if (diffSeconds < 5) return 'just now'
  if (diffSeconds < 60) return `${diffSeconds}s ago`

  const diffMinutes = Math.floor(diffSeconds / 60)
  if (diffMinutes < 60) return `${diffMinutes}m ago`

  const diffHours = Math.floor(diffMinutes / 60)
  if (diffHours < 24) return `${diffHours}h ago`

  const diffDays = Math.floor(diffHours / 24)
  if (diffDays < 7) return `${diffDays}d ago`

  const diffWeeks = Math.floor(diffDays / 7)
  return `${diffWeeks}w ago`
}

export function statusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'running':
      return 'text-blue-400'
    case 'complete':
    case 'completed':
    case 'success':
      return 'text-green-400'
    case 'failed':
    case 'error':
      return 'text-red-400'
    case 'blocked':
    case 'warning':
      return 'text-yellow-400'
    case 'queued':
      return 'text-purple-400'
    case 'idle':
    case 'offline':
    case 'cancelled':
    default:
      return 'text-gray-400'
  }
}

export function statusBg(status: string): string {
  switch (status.toLowerCase()) {
    case 'running':
      return 'bg-blue-500/10 border-blue-500/30'
    case 'complete':
    case 'completed':
    case 'success':
      return 'bg-green-500/10 border-green-500/30'
    case 'failed':
    case 'error':
      return 'bg-red-500/10 border-red-500/30'
    case 'blocked':
    case 'warning':
      return 'bg-yellow-500/10 border-yellow-500/30'
    case 'queued':
      return 'bg-purple-500/10 border-purple-500/30'
    case 'idle':
      return 'bg-gray-500/10 border-gray-500/30'
    case 'offline':
    case 'cancelled':
    default:
      return 'bg-gray-800/50 border-gray-700/30'
  }
}

export function formatCost(usd: number): string {
  if (usd === 0) return '$0.00'
  if (usd < 0.0001) return `$${usd.toExponential(2)}`
  if (usd < 0.01) return `$${usd.toFixed(4)}`
  if (usd < 1) return `$${usd.toFixed(3)}`
  if (usd < 100) return `$${usd.toFixed(2)}`
  return `$${usd.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export function formatTokens(n: number): string {
  if (n < 1000) return n.toString()
  if (n < 1_000_000) return `${(n / 1000).toFixed(1)}k`
  return `${(n / 1_000_000).toFixed(2)}M`
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function truncate(str: string, maxLen: number): string {
  if (str.length <= maxLen) return str
  return str.slice(0, maxLen - 1) + '…'
}
