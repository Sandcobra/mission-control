'use client'

import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from 'react'
import { useWebSocket } from '@/lib/websocket'

const MAX_EVENTS = 100

export interface LiveEvent {
  id: string
  timestamp: string
  channel: 'task' | 'agent'
  event_type: string
  agent_key?: string
  task_key?: string
  message: string
  raw: unknown
}

interface RawEventPayload {
  event_type?: string
  type?: string
  agent_key?: string
  task_key?: string
  message?: string
  [key: string]: unknown
}

let eventCounter = 0
function makeId(): string {
  return `evt_${Date.now()}_${eventCounter++}`
}

interface LiveEventsContextValue {
  events: LiveEvent[]
}

const LiveEventsContext = createContext<LiveEventsContextValue>({ events: [] })

export function useLiveEvents() {
  return useContext(LiveEventsContext)
}

export function LiveEventsProvider({ children }: { children: ReactNode }) {
  const [events, setEvents] = useState<LiveEvent[]>([])

  const addEvent = useCallback((event: LiveEvent) => {
    setEvents((prev) => [event, ...prev].slice(0, MAX_EVENTS))
  }, [])

  const handleTaskMessage = useCallback(
    (data: unknown) => {
      const payload = data as RawEventPayload
      addEvent({
        id: makeId(),
        timestamp: new Date().toISOString(),
        channel: 'task',
        event_type: payload.event_type ?? payload.type ?? 'update',
        agent_key: payload.agent_key,
        task_key: payload.task_key,
        message: payload.message ?? JSON.stringify(data).slice(0, 120),
        raw: data,
      })
    },
    [addEvent]
  )

  const handleAgentMessage = useCallback(
    (data: unknown) => {
      const payload = data as RawEventPayload
      addEvent({
        id: makeId(),
        timestamp: new Date().toISOString(),
        channel: 'agent',
        event_type: payload.event_type ?? payload.type ?? 'heartbeat',
        agent_key: payload.agent_key,
        message: payload.message ?? JSON.stringify(data).slice(0, 120),
        raw: data,
      })
    },
    [addEvent]
  )

  useWebSocket('task_updates', handleTaskMessage)
  useWebSocket('agent_updates', handleAgentMessage)

  return (
    <LiveEventsContext.Provider value={{ events }}>
      {children}
    </LiveEventsContext.Provider>
  )
}
