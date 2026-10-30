import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  CheckCircle2,
  Clock,
  ArrowRight,
  ShieldAlert,
  FolderGit2,
  AlertTriangle,
} from 'lucide-react';
import { api } from '../services/api';
import { eventStream } from '../services/events';
import {
  OrganizationStatus,
  ApprovalRequest,
  Project,
  SystemEvent,
} from '../types';
import { Badge } from '../components/common/Badge';
import { LiveActivityStream } from '../components/common/LiveActivityStream';
import { OrgGraph } from '../components/common/OrgGraph';

export const CommandCenter: React.FC = () => {
  const [status, setStatus] = useState<OrganizationStatus | null>(null);
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [events, setEvents] = useState<SystemEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [statusRes, approvalsRes, projectsRes, eventsRes] = await Promise.all([
        api.getOrgStatus().catch(() => null),
        api.getApprovals('PENDING').catch(() => []),
        api.getProjects().catch(() => []),
        api.getEvents(15).catch(() => []),
      ]);

      if (statusRes) setStatus(statusRes);
      setApprovals(approvalsRes);
      setProjects(projectsRes);
      setEvents(eventsRes);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();

    // Subscribe to real-time events to auto-refresh data
    const unsub = eventStream.subscribe((newEvent) => {
      setEvents((prev) => [newEvent, ...prev.slice(0, 24)]);

      // If project/task/approval event happens, refresh
      if (
        newEvent.event_type.startsWith('approval.') ||
        newEvent.event_type.startsWith('project.') ||
        newEvent.event_type.startsWith('task.')
      ) {
        loadData();
      }
    });

    return () => unsub();
  }, []);

  const handleQuickDecision = async (
    approvalId: string,
    decision: 'APPROVE' | 'REJECT' | 'REQUEST_CHANGES'
  ) => {
    setActionLoading(approvalId);
    try {
      await api.submitApprovalDecision(approvalId, decision);
      await loadData();
    } catch (err: any) {
      alert(`Approval decision failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const activeProjects = projects.filter(
    (p) => !['COMPLETED', 'REJECTED', 'CANCELLED'].includes(p.status)
  );

  return (
    <div className="space-y-6">
      {/* Top Banner / Headline */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-gray-200">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-gray-900">
            Command Center
          </h1>
          <p className="text-xs text-gray-500 font-mono mt-0.5">
            Operational status and real-time multi-agent activity
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/chat"
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-medium bg-gray-900 text-white hover:bg-gray-800 transition-colors shadow-xs"
          >
            <span>Chat with PA</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* System Infrastructure Indicators */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 font-mono text-xs">
        <div className="bg-white border border-gray-200 rounded p-3 shadow-2xs">
          <div className="text-[10px] text-gray-400 uppercase tracking-wider mb-1">Backend</div>
          <div className="flex items-center gap-1.5 font-medium text-gray-900">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>FastAPI 2.0</span>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded p-3 shadow-2xs">
          <div className="text-[10px] text-gray-400 uppercase tracking-wider mb-1">Database</div>
          <div className="flex items-center gap-1.5 font-medium text-gray-900">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>PostgreSQL 16</span>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded p-3 shadow-2xs">
          <div className="text-[10px] text-gray-400 uppercase tracking-wider mb-1">Ollama LLM</div>
          <div className="flex items-center gap-1.5 font-medium text-gray-900">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>gemma3:4b</span>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded p-3 shadow-2xs">
          <div className="text-[10px] text-gray-400 uppercase tracking-wider mb-1">Techy Runtime</div>
          <div className="flex items-center gap-1.5 font-medium text-gray-900">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>SSH (VICKY)</span>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded p-3 shadow-2xs col-span-2 sm:col-span-1">
          <div className="text-[10px] text-gray-400 uppercase tracking-wider mb-1">Event Stream</div>
          <div className="flex items-center gap-1.5 font-medium text-gray-900">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>SSE Active</span>
          </div>
        </div>
      </div>

      {/* Agents Status Cards */}
      <div>
        <div className="text-xs font-mono uppercase tracking-wider text-gray-400 mb-2 font-medium">
          Agent Status
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* PA */}
          <div className="bg-white border border-gray-200 rounded-lg p-3.5 shadow-2xs">
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono font-semibold text-gray-900 text-sm">PA</span>
              <Badge status={status?.agents_status?.['pa'] || 'ONLINE'} size="sm" />
            </div>
            <div className="text-xs text-gray-500">Personal Assistant</div>
            <div className="text-[11px] font-mono text-gray-400 mt-2 truncate">
              Liaison & Triage Coordinator
            </div>
          </div>

          {/* ARCHY */}
          <div className="bg-white border border-gray-200 rounded-lg p-3.5 shadow-2xs">
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono font-semibold text-gray-900 text-sm">ARCHY</span>
              <Badge status={status?.agents_status?.['archy'] || 'IDLE'} size="sm" />
            </div>
            <div className="text-xs text-gray-500">Project Architect</div>
            <div className="text-[11px] font-mono text-gray-400 mt-2 truncate">
              Blueprints & Task Planning
            </div>
          </div>

          {/* ELDER */}
          <div className="bg-white border border-gray-200 rounded-lg p-3.5 shadow-2xs">
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono font-semibold text-gray-900 text-sm">ELDER</span>
              <Badge status={status?.agents_status?.['elder'] || 'IDLE'} size="sm" />
            </div>
            <div className="text-xs text-gray-500">Senior Advisor</div>
            <div className="text-[11px] font-mono text-gray-400 mt-2 truncate">
              9-Dimension Review & Governance
            </div>
          </div>

          {/* TECHY */}
          <div className="bg-white border border-gray-200 rounded-lg p-3.5 shadow-2xs">
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono font-semibold text-gray-900 text-sm">TECHY</span>
              <Badge status={status?.agents_status?.['techy'] || 'IDLE'} size="sm" />
            </div>
            <div className="text-xs text-gray-500">Engineer / Sysadmin</div>
            <div className="text-[11px] font-mono text-gray-400 mt-2 truncate">
              Server Operations & Tools
            </div>
          </div>
        </div>
      </div>

      {/* Prominent Pending Approvals Alert (Section 6 & 13) */}
      {approvals.length > 0 && (
        <div className="border border-amber-200 bg-amber-50/50 rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-600" />
              <span className="font-mono text-xs font-semibold text-amber-900 uppercase tracking-wide">
                Approval Required ({approvals.length})
              </span>
            </div>
            <Link
              to="/approvals"
              className="text-xs font-mono text-amber-700 hover:text-amber-900 underline flex items-center gap-1"
            >
              <span>View all</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="space-y-3">
            {approvals.map((req) => (
              <div
                key={req.id}
                className="bg-white border border-amber-200 rounded-md p-3.5 text-xs shadow-2xs"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                  <div className="font-mono font-medium text-gray-900">{req.action}</div>
                  <Badge status={`RISK: ${req.risk_level}`} size="sm" />
                </div>

                {req.reason && (
                  <p className="text-gray-600 mb-3 font-sans leading-relaxed">
                    {req.reason}
                  </p>
                )}

                <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-gray-100">
                  <button
                    disabled={actionLoading === req.id}
                    onClick={() => handleQuickDecision(req.id, 'APPROVE')}
                    className="px-3 py-1 bg-emerald-600 text-white font-mono text-xs font-medium rounded hover:bg-emerald-700 transition-colors disabled:opacity-50"
                  >
                    {actionLoading === req.id ? 'Processing...' : 'Approve Execution'}
                  </button>
                  <button
                    disabled={actionLoading === req.id}
                    onClick={() => handleQuickDecision(req.id, 'REQUEST_CHANGES')}
                    className="px-3 py-1 bg-amber-600 text-white font-mono text-xs font-medium rounded hover:bg-amber-700 transition-colors disabled:opacity-50"
                  >
                    Request Changes
                  </button>
                  <button
                    disabled={actionLoading === req.id}
                    onClick={() => handleQuickDecision(req.id, 'REJECT')}
                    className="px-3 py-1 bg-rose-600 text-white font-mono text-xs font-medium rounded hover:bg-rose-700 transition-colors disabled:opacity-50"
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Grid: Active Projects + Live Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Projects (2 columns on lg) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div className="text-xs font-mono uppercase tracking-wider text-gray-400 font-medium">
              Active Projects ({activeProjects.length})
            </div>
            <Link
              to="/projects"
              className="text-xs font-mono text-gray-500 hover:text-gray-900 flex items-center gap-1"
            >
              <span>All projects</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          {activeProjects.length === 0 ? (
            <div className="bg-white border border-gray-200 rounded-lg p-6 text-center text-xs font-mono text-gray-400">
              No active projects in progress.
            </div>
          ) : (
            <div className="space-y-3">
              {activeProjects.map((p) => (
                <div
                  key={p.id}
                  className="bg-white border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors shadow-2xs"
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div>
                      <Link
                        to={`/projects`}
                        className="font-medium text-gray-900 hover:text-blue-600 text-sm font-sans"
                      >
                        {p.name}
                      </Link>
                      {p.description && (
                        <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                          {p.description}
                        </p>
                      )}
                    </div>
                    <Badge status={p.status} />
                  </div>

                  <div className="flex items-center justify-between text-[11px] font-mono text-gray-400 pt-2 border-t border-gray-100">
                    <span className="flex items-center gap-1">
                      <FolderGit2 className="w-3 h-3 text-gray-400" />
                      <span>Created by {p.created_by?.toUpperCase() || 'PA'}</span>
                    </span>
                    <span>
                      {new Date(p.created_at).toLocaleDateString([], {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Organizational Graph */}
          <div className="mt-6">
            <OrgGraph />
          </div>
        </div>

        {/* Live Activity Stream (1 column on lg) */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="text-xs font-mono uppercase tracking-wider text-gray-400 font-medium">
              Live Activity Stream
            </div>
            <Link
              to="/conversations"
              className="text-xs font-mono text-gray-500 hover:text-gray-900 flex items-center gap-1"
            >
              <span>Full stream</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-3.5 shadow-2xs">
            <LiveActivityStream events={events} maxItems={8} />
          </div>
        </div>
      </div>
    </div>
  );
};
