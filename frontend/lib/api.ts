import axios from 'axios'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ─── Types ────────────────────────────────────────────────────────────────────

export type AgentStatus = 'idle' | 'running' | 'blocked' | 'offline' | 'error'
export type TaskStatus = 'queued' | 'running' | 'blocked' | 'failed' | 'complete' | 'cancelled'
export type TaskPriority = 'low' | 'normal' | 'high' | 'critical'

export interface Agent {
  agent_id: string
  agent_key: string
  name: string
  role: string
  runtime_type: string
  model_name: string
  status: AgentStatus
  host: string
  version: string
  current_task_id: string | null
  current_task_title: string | null
  current_task_progress: number | null
  last_heartbeat: string
  created_at: string
  metadata: Record<string, unknown>
}

export interface Task {
  task_id: string
  task_key: string
  title: string
  description: string | null
  status: TaskStatus
  priority: TaskPriority
  assigned_agent_id: string | null
  assigned_agent_name: string | null
  assigned_agent_key: string | null
  progress: number
  current_step: string | null
  total_steps: number | null
  completed_steps: number | null
  result_summary: string | null
  error_message: string | null
  input_data: Record<string, unknown> | null
  output_data: Record<string, unknown> | null
  cost_usd: number | null
  input_tokens: number | null
  output_tokens: number | null
  created_at: string
  started_at: string | null
  completed_at: string | null
  updated_at: string
  metadata: Record<string, unknown>
}

export interface TaskEvent {
  event_id: string
  task_id: string
  agent_id: string | null
  agent_key: string | null
  agent_name: string | null
  event_type: string
  message: string
  data: Record<string, unknown> | null
  created_at: string
}

export interface Artifact {
  artifact_id: string
  task_id: string
  name: string
  artifact_type: string
  content_type: string
  size_bytes: number | null
  url: string | null
  content: string | null
  created_at: string
}

export interface AgentRun {
  run_id: string
  agent_id: string
  task_id: string | null
  started_at: string
  ended_at: string | null
  status: string
  input_tokens: number
  output_tokens: number
  cost_usd: number
  model_name: string
}

export interface OverviewMetrics {
  agents_total: number
  agents_online: number
  agents_idle: number
  agents_running: number
  agents_blocked: number
  agents_offline: number
  agents_error: number
  tasks_total: number
  tasks_queued: number
  tasks_running: number
  tasks_blocked: number
  tasks_failed_24h: number
  tasks_completed_24h: number
  tasks_failed_total: number
  tasks_completed_total: number
  spend_today_usd: number
  spend_total_usd: number
}

export interface CostByDay {
  date: string
  cost_usd: number
  input_tokens: number
  output_tokens: number
  task_count: number
}

export interface CostByAgent {
  agent_id: string
  agent_key: string
  agent_name: string
  cost_usd: number
  input_tokens: number
  output_tokens: number
  run_count: number
}

export interface CostMetrics {
  total_usd: number
  today_usd: number
  by_day: CostByDay[]
  by_agent: CostByAgent[]
}

export interface FailureItem {
  task_id: string
  task_key: string
  title: string
  agent_name: string | null
  error_message: string | null
  failed_at: string
}

export interface ErrorType {
  error_type: string
  count: number
}

export interface StaleAgent {
  agent_id: string
  agent_key: string
  name: string
  last_heartbeat: string
  status: AgentStatus
}

export interface StuckTask {
  task_id: string
  task_key: string
  title: string
  agent_name: string | null
  started_at: string
  running_for_seconds: number
}

export interface FailureMetrics {
  recent_failures: FailureItem[]
  top_error_types: ErrorType[]
  stale_agents: StaleAgent[]
  stuck_tasks: StuckTask[]
  failure_count_24h: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

// ─── API Functions ────────────────────────────────────────────────────────────

export async function fetchAgents(status?: string): Promise<Agent[]> {
  const params: Record<string, string> = {}
  if (status && status !== 'all') params.status = status
  const res = await apiClient.get<Agent[]>('/api/agents', { params })
  return res.data
}

export async function fetchAgent(id: string): Promise<Agent> {
  const res = await apiClient.get<Agent>(`/api/agents/${id}`)
  return res.data
}

export interface FetchTasksParams {
  status?: string
  agent_id?: string
  limit?: number
  offset?: number
  search?: string
}

export async function fetchTasks(params: FetchTasksParams = {}): Promise<PaginatedResponse<Task>> {
  const queryParams: Record<string, string | number> = {}
  if (params.status && params.status !== 'all') queryParams.status = params.status
  if (params.agent_id) queryParams.agent_id = params.agent_id
  if (params.limit !== undefined) queryParams.limit = params.limit
  if (params.offset !== undefined) queryParams.offset = params.offset
  if (params.search) queryParams.search = params.search
  const res = await apiClient.get<PaginatedResponse<Task>>('/api/tasks', { params: queryParams })
  return res.data
}

export async function fetchTask(id: string): Promise<Task> {
  const res = await apiClient.get<Task>(`/api/tasks/${id}`)
  return res.data
}

export async function fetchTaskEvents(taskId: string): Promise<TaskEvent[]> {
  const res = await apiClient.get<TaskEvent[]>(`/api/tasks/${taskId}/events`)
  return res.data
}

export async function fetchTaskArtifacts(taskId: string): Promise<Artifact[]> {
  const res = await apiClient.get<Artifact[]>(`/api/tasks/${taskId}/artifacts`)
  return res.data
}

export async function fetchOverviewMetrics(): Promise<OverviewMetrics> {
  const res = await apiClient.get<OverviewMetrics>('/api/metrics/overview')
  return res.data
}

export async function fetchCostMetrics(): Promise<CostMetrics> {
  const res = await apiClient.get<CostMetrics>('/api/metrics/costs')
  return res.data
}

export async function fetchFailureMetrics(): Promise<FailureMetrics> {
  const res = await apiClient.get<FailureMetrics>('/api/metrics/failures')
  return res.data
}
