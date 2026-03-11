'use client'

import { useEffect, useRef, useCallback } from 'react'

export const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'

const BASE_RECONNECT_DELAY_MS = 1000
const MAX_RECONNECT_DELAY_MS = 30000

export function useWebSocket(
  channel: string,
  onMessage: (data: unknown) => void,
  enabled: boolean = true
): void {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const attemptsRef = useRef(0)
  const onMessageRef = useRef(onMessage)
  const mountedRef = useRef(true)
  // Store connect in a ref to break the circular useCallback dependency
  const connectRef = useRef<() => void>(() => {})

  // Keep onMessage ref current to avoid stale closures
  useEffect(() => {
    onMessageRef.current = onMessage
  }, [onMessage])

  const connect = useCallback(() => {
    if (!mountedRef.current || !enabled) return

    const url = `${WS_BASE_URL}/ws/${channel}`

    const scheduleReconnect = () => {
      if (!mountedRef.current) return
      const delay = Math.min(
        BASE_RECONNECT_DELAY_MS * 2 ** attemptsRef.current,
        MAX_RECONNECT_DELAY_MS
      )
      attemptsRef.current += 1
      reconnectTimerRef.current = setTimeout(() => {
        if (mountedRef.current) connectRef.current()
      }, delay)
    }

    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        if (!mountedRef.current) return
        attemptsRef.current = 0
      }

      ws.onmessage = (event: MessageEvent) => {
        if (!mountedRef.current) return
        try {
          const data = JSON.parse(event.data as string)
          onMessageRef.current(data)
        } catch {
          onMessageRef.current(event.data)
        }
      }

      ws.onclose = () => {
        if (!mountedRef.current) return
        wsRef.current = null
        scheduleReconnect()
      }

      ws.onerror = () => {
        ws.close()
      }
    } catch {
      scheduleReconnect()
    }
  }, [channel, enabled])

  // Keep connectRef in sync
  useEffect(() => {
    connectRef.current = connect
  }, [connect])

  useEffect(() => {
    mountedRef.current = true

    if (enabled) {
      connect()
    }

    return () => {
      mountedRef.current = false

      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
        reconnectTimerRef.current = null
      }

      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [connect, enabled])
}
