import {
  Agent,
  Project,
  Task,
  Message,
  SystemEvent,
  ApprovalRequest,
  DecisionRecord,
  MemoryItem,
  ServerDiscovery,
  OrganizationStatus,
  ProjectTimelineItem,
  PAResponse,
} from '../types';

const API_BASE = import.meta.env.VITE_BACKEND_URL ? `${import.meta.env.VITE_BACKEND_URL}/api` : '/api';

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  let url = `${API_BASE}${endpoint}`;
  if (url.startsWith('/')) {
    const origin = typeof window !== 'undefined' && window.location?.origin && window.location.origin !== 'null'
      ? window.location.origin
      : 'http://localhost:8090';
    url = `${origin}${url}`;
  }
  const headers = {
    'Content-Type': 'application/json',
    ...(options?.headers || {}),
  };

  try {
    const res = await fetch(url, { ...options, headers });
    if (!res.ok) {
      let errorDetail = `Request failed: ${res.statusText} (${res.status})`;
      try {
        const errorJson = await res.json();
        if (errorJson.detail) {
          errorDetail = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
        }
      } catch {
        // Fallback to status text
      }
      throw new Error(errorDetail);
    }
    return (await res.json()) as T;
  } catch (err: any) {
    console.error(`API Error on ${endpoint}:`, err);
    throw err;
  }
}

export const api = {
  // Health
  checkHealth: () => request<{ status: string; service: string }>('/health'),

  // Organization Workflow
  getOrgStatus: () => request<OrganizationStatus>('/org/status'),
  chatWithPA: (message: string, project_id?: string) =>
    request<PAResponse>('/org/chat', {
      method: 'POST',
      body: JSON.stringify({ message, project_id }),
    }),
  submitApprovalDecision: (
    approvalId: string,
    decision: 'APPROVE' | 'REJECT' | 'REQUEST_CHANGES',
    notes?: string
  ) =>
    request<PAResponse>(`/org/approvals/${approvalId}/decide`, {
      method: 'POST',
      body: JSON.stringify({ decision, notes, approved_by: 'user' }),
    }),
  getProjectTimeline: (projectId: string) =>
    request<ProjectTimelineItem[]>(`/org/projects/${projectId}/timeline`),
  getDecisions: (projectId?: string) => {
    const q = projectId ? `?project_id=${projectId}` : '';
    return request<DecisionRecord[]>(`/org/decisions${q}`);
  },

  // Agents
  getAgents: () => request<Agent[]>('/agents'),
  getAgent: (id: string) => request<Agent>(`/agents/${id}`),

  // Projects
  getProjects: () => request<Project[]>('/projects'),
  getProject: (id: string) => request<Project>(`/projects/${id}`),

  // Tasks
  getTasks: (projectId?: string, status?: string) => {
    const params = new URLSearchParams();
    if (projectId) params.append('project_id', projectId);
    if (status) params.append('status', status);
    const q = params.toString() ? `?${params.toString()}` : '';
    return request<Task[]>(`/tasks${q}`);
  },
  getTask: (id: string) => request<Task>(`/tasks/${id}`),

  // Messages / Conversations
  getMessages: (params?: { sender_id?: string; receiver_id?: string; project_id?: string; limit?: number }) => {
    const sp = new URLSearchParams();
    if (params?.sender_id) sp.append('sender_id', params.sender_id);
    if (params?.receiver_id) sp.append('receiver_id', params.receiver_id);
    if (params?.project_id) sp.append('project_id', params.project_id);
    if (params?.limit) sp.append('limit', params.limit.toString());
    const q = sp.toString() ? `?${sp.toString()}` : '';
    return request<Message[]>(`/messages${q}`);
  },

  // Approvals
  getApprovals: (status?: string) => {
    const q = status ? `?status=${status}` : '';
    return request<ApprovalRequest[]>(`/approvals${q}`);
  },

  // Events
  getEvents: (limit: number = 50) => request<SystemEvent[]>(`/events?limit=${limit}`),

  // Memory
  getMemories: (type?: string, limit: number = 100) => {
    const params = new URLSearchParams();
    if (type) params.append('type', type);
    params.append('limit', limit.toString());
    return request<MemoryItem[]>(`/memory?${params.toString()}`);
  },

  // Techy & Server Operations
  getServerDiscovery: (forceRefresh: boolean = false) =>
    request<{ discovery: ServerDiscovery; cached: boolean }>(
      `/techy/discovery?force_refresh=${forceRefresh}`
    ),
  getTechyRunDetails: (taskId: string) =>
    request<any>(`/techy/runs/${taskId}`),
  getTechyTools: () => request<{ count: number; tools: any[] }>('/techy/tools'),
  executeTechyTask: (instruction: string, maxSteps: number = 5) =>
    request<any>('/techy/execute', {
      method: 'POST',
      body: JSON.stringify({ instruction, max_steps: maxSteps }),
    }),
};
