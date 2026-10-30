export interface Agent {
  id: string;
  name: string;
  role: string;
  description?: string;
  personality?: string;
  objectives?: string[];
  system_prompt?: string;
  model_name?: string;
  status: string;
  created_at: string;
  updated_at?: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  status: 'IDEA' | 'PLANNING' | 'REVIEW' | 'AWAITING_APPROVAL' | 'APPROVED' | 'EXECUTING' | 'VERIFYING' | 'COMPLETED' | 'BLOCKED' | 'REJECTED';
  created_by?: string;
  assigned_to?: string;
  objectives?: string[];
  metadata_json?: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

export interface Task {
  id: string;
  title: string;
  description?: string;
  created_by?: string;
  assigned_to?: string;
  parent_task_id?: string | null;
  project_id?: string | null;
  status: 'PENDING' | 'PLANNING' | 'RUNNING' | 'WAITING' | 'BLOCKED' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  priority: string;
  progress: number;
  result?: Record<string, any> | null;
  error?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  updated_at?: string;
}

export interface Message {
  id: string;
  sender_id: string;
  receiver_id: string;
  content: string;
  message_type: string;
  task_id?: string | null;
  project_id?: string | null;
  status: string;
  metadata_json?: Record<string, any>;
  created_at: string;
}

export interface SystemEvent {
  id: string;
  event_type: string;
  source: string;
  related_agent_id?: string | null;
  related_task_id?: string | null;
  related_project_id?: string | null;
  payload: Record<string, any>;
  created_at: string;
}

export interface ApprovalRequest {
  id: string;
  project_id?: string | null;
  task_id?: string | null;
  requesting_agent_id: string;
  action: string;
  reason?: string;
  risk_level: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'REQUEST_CHANGES';
  approved_by?: string | null;
  rejection_reason?: string | null;
  created_at: string;
  decided_at?: string | null;
}

export interface DecisionRecord {
  id: string;
  project_id?: string | null;
  task_id?: string | null;
  title: string;
  category: string;
  status: string;
  proposed_by: string;
  reviewed_by?: string | null;
  approved_by?: string | null;
  decision: string;
  reason?: string | null;
  alternatives_considered?: string[];
  risks_identified?: string[];
  review_notes?: string | null;
  created_at: string;
}

export interface MemoryItem {
  id: string;
  agent_id: string;
  type: string;
  content: string;
  importance: number;
  metadata_json?: Record<string, any>;
  created_at: string;
}

export interface ServerDiscovery {
  hostname?: string;
  os?: string;
  kernel?: string;
  uptime?: string;
  cpu?: {
    model?: string;
    cores?: number;
    usage_percent?: number;
  };
  memory?: {
    total_mb?: number;
    used_mb?: number;
    free_mb?: number;
    usage_percent?: number;
  };
  disk?: {
    total_gb?: number;
    used_gb?: number;
    free_gb?: number;
    usage_percent?: number;
  };
  docker?: {
    installed?: boolean;
    running?: boolean;
    containers_count?: number;
    running_count?: number;
    containers?: Array<{
      id: string;
      names: string;
      image: string;
      status: string;
      state: string;
    }>;
  };
  network?: {
    ip_addresses?: string[];
    listening_ports?: number[];
  };
  services?: Record<string, string>;
}

export interface OrganizationStatus {
  active_projects_count: number;
  pending_approvals_count: number;
  running_tasks_count: number;
  agents_status: Record<string, string>;
  recent_critical_events: Array<Record<string, any>>;
}

export interface ProjectTimelineItem {
  timestamp: string;
  type: string;
  source: string;
  title: string;
  details: Record<string, any>;
}

export interface PAResponse {
  message: string;
  intent: string;
  action_taken: string;
  project_id?: string | null;
  task_id?: string | null;
  approval_id?: string | null;
  requires_human_approval: boolean;
  proposal_summary?: string | null;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
}
