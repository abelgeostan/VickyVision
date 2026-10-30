import React, { useEffect, useState } from 'react';
import { Filter, ArrowUpDown, RefreshCw, X, MessageSquare, Activity } from 'lucide-react';
import { api } from '../services/api';
import { eventStream } from '../services/events';
import { Message, SystemEvent } from '../types';
import { Badge } from '../components/common/Badge';

interface UnifiedStreamItem {
  id: string;
  sourceType: 'MESSAGE' | 'EVENT';
  category: string;
  agent: string;
  title: string;
  body: string;
  timestamp: string;
  status?: string;
  projectId?: string | null;
  taskId?: string | null;
  raw: any;
}

export const Conversations: React.FC = () => {
  const [items, setItems] = useState<UnifiedStreamItem[]>([]);
  const [agentFilter, setAgentFilter] = useState<string>('ALL');
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [selectedItem, setSelectedItem] = useState<UnifiedStreamItem | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const loadData = async () => {
    try {
      const [messagesRes, eventsRes] = await Promise.all([
        api.getMessages({ limit: 100 }).catch(() => []),
        api.getEvents(100).catch(() => []),
      ]);

      const unified: UnifiedStreamItem[] = [];

      messagesRes.forEach((m) => {
        unified.push({
          id: `msg-${m.id}`,
          sourceType: 'MESSAGE',
          category: 'MESSAGE',
          agent: m.sender_id,
          title: `Message: ${m.sender_id.toUpperCase()} → ${m.receiver_id.toUpperCase()}`,
          body: m.content,
          timestamp: m.created_at,
          status: m.status,
          projectId: m.project_id,
          taskId: m.task_id,
          raw: m,
        });
      });

      eventsRes.forEach((e) => {
        let cat = 'EVENT';
        if (e.event_type.startsWith('task.')) cat = 'TASK';
        else if (e.event_type.startsWith('techy.tool') || e.event_type.startsWith('techy.direct')) cat = 'TOOL';
        else if (e.event_type.startsWith('decision.')) cat = 'DECISION';
        else if (e.event_type.startsWith('approval.')) cat = 'APPROVAL';

        const agentName = e.related_agent_id || e.source;

        unified.push({
          id: `evt-${e.id}`,
          sourceType: 'EVENT',
          category: cat,
          agent: agentName,
          title: `Event: ${e.event_type}`,
          body:
            e.payload?.title ||
            e.payload?.summary ||
            e.payload?.tool ||
            e.payload?.action ||
            JSON.stringify(e.payload),
          timestamp: e.created_at,
          status: e.payload?.status || 'EMITTED',
          projectId: e.related_project_id,
          taskId: e.related_task_id,
          raw: e,
        });
      });

      // Sort chronological descending
      unified.sort(
        (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );

      setItems(unified);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();

    const unsub = eventStream.subscribe((e) => {
      let cat = 'EVENT';
      if (e.event_type.startsWith('task.')) cat = 'TASK';
      else if (e.event_type.startsWith('techy.tool')) cat = 'TOOL';
      else if (e.event_type.startsWith('decision.')) cat = 'DECISION';
      else if (e.event_type.startsWith('approval.')) cat = 'APPROVAL';

      const newItem: UnifiedStreamItem = {
        id: `evt-${e.id}`,
        sourceType: 'EVENT',
        category: cat,
        agent: e.related_agent_id || e.source,
        title: `Event: ${e.event_type}`,
        body: e.payload?.title || e.payload?.summary || JSON.stringify(e.payload),
        timestamp: e.created_at,
        status: e.payload?.status || 'EMITTED',
        projectId: e.related_project_id,
        taskId: e.related_task_id,
        raw: e,
      };

      setItems((prev) => [newItem, ...prev]);
    });

    return () => unsub();
  }, []);

  const filteredItems = items.filter((item) => {
    if (agentFilter !== 'ALL') {
      if (item.agent.toLowerCase() !== agentFilter.toLowerCase()) return false;
    }
    if (categoryFilter !== 'ALL') {
      if (item.category !== categoryFilter) return false;
    }
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-gray-200">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-gray-900">
            Conversation Explorer
          </h1>
          <p className="text-xs text-gray-500 font-mono mt-0.5">
            Inter-agent communication and organization event stream
          </p>
        </div>

        <button
          onClick={loadData}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-gray-200 text-xs font-mono text-gray-700 bg-white hover:bg-gray-50 transition-colors shadow-2xs self-start"
        >
          <RefreshCw className="w-3.5 h-3.5 text-gray-500" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filters (Section 9) */}
      <div className="flex flex-wrap items-center gap-4 bg-white p-3 rounded-lg border border-gray-200 shadow-2xs text-xs font-mono">
        <div className="flex items-center gap-2">
          <span className="text-gray-400">Agent:</span>
          {['ALL', 'USER', 'PA', 'ARCHY', 'ELDER', 'TECHY'].map((ag) => (
            <button
              key={ag}
              onClick={() => setAgentFilter(ag)}
              className={`px-2 py-0.5 rounded text-[11px] transition-colors ${
                agentFilter === ag
                  ? 'bg-gray-900 text-white font-medium'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {ag}
            </button>
          ))}
        </div>

        <div className="h-4 w-px bg-gray-200 hidden sm:block" />

        <div className="flex items-center gap-2">
          <span className="text-gray-400">Type:</span>
          {['ALL', 'MESSAGE', 'TASK', 'TOOL', 'DECISION', 'APPROVAL', 'EVENT'].map((cat) => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              className={`px-2 py-0.5 rounded text-[11px] transition-colors ${
                categoryFilter === cat
                  ? 'bg-gray-900 text-white font-medium'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Unified Stream List */}
      <div className="bg-white border border-gray-200 rounded-lg shadow-2xs overflow-hidden">
        {filteredItems.length === 0 ? (
          <div className="p-8 text-center text-xs font-mono text-gray-400">
            No entries match the selected filters.
          </div>
        ) : (
          <div className="divide-y divide-gray-100 font-mono text-xs">
            {filteredItems.map((item) => {
              const time = new Date(item.timestamp).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
              });
              const date = new Date(item.timestamp).toLocaleDateString([], {
                month: 'short',
                day: 'numeric',
              });

              return (
                <div
                  key={item.id}
                  onClick={() => setSelectedItem(item)}
                  className="p-3.5 hover:bg-gray-50/80 cursor-pointer transition-colors flex items-start justify-between gap-4"
                >
                  <div className="flex items-start gap-3 min-w-0 flex-1">
                    <div className="mt-0.5">
                      {item.sourceType === 'MESSAGE' ? (
                        <MessageSquare className="w-4 h-4 text-gray-500" />
                      ) : (
                        <Activity className="w-4 h-4 text-blue-500" />
                      )}
                    </div>

                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold text-gray-900 uppercase">
                          {item.agent}
                        </span>
                        <span className="text-[10px] text-gray-400 px-1.5 py-0.2 rounded bg-gray-100 border border-gray-200">
                          {item.category}
                        </span>
                        {item.status && <Badge status={item.status} size="sm" />}
                      </div>

                      <div className="text-gray-700 text-xs truncate font-sans">
                        {item.body}
                      </div>

                      {(item.projectId || item.taskId) && (
                        <div className="mt-1 flex items-center gap-3 text-[10px] text-gray-400">
                          {item.projectId && <span>Project: {item.projectId.slice(0, 8)}...</span>}
                          {item.taskId && <span>Task: {item.taskId.slice(0, 8)}...</span>}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="text-[11px] text-gray-400 shrink-0 text-right">
                    <div>{time}</div>
                    <div className="text-[9px]">{date}</div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Item Details Drawer/Modal */}
      {selectedItem && (
        <div className="fixed inset-0 bg-black/30 z-40 flex items-center justify-center p-4">
          <div className="bg-white border border-gray-200 rounded-lg max-w-2xl w-full p-5 shadow-lg space-y-4 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-gray-100">
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm font-semibold text-gray-900">
                  {selectedItem.title}
                </span>
                <Badge status={selectedItem.category} size="sm" />
              </div>
              <button
                onClick={() => setSelectedItem(null)}
                className="text-gray-400 hover:text-gray-700 p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs font-mono">
              <div className="grid grid-cols-2 gap-3 bg-gray-50 p-3 rounded border border-gray-100">
                <div>
                  <span className="text-gray-400">Agent:</span>{' '}
                  <span className="font-medium text-gray-800">{selectedItem.agent}</span>
                </div>
                <div>
                  <span className="text-gray-400">Timestamp:</span>{' '}
                  <span className="text-gray-800">
                    {new Date(selectedItem.timestamp).toLocaleString()}
                  </span>
                </div>
                {selectedItem.projectId && (
                  <div>
                    <span className="text-gray-400">Project ID:</span>{' '}
                    <span className="text-gray-800">{selectedItem.projectId}</span>
                  </div>
                )}
                {selectedItem.taskId && (
                  <div>
                    <span className="text-gray-400">Task ID:</span>{' '}
                    <span className="text-gray-800">{selectedItem.taskId}</span>
                  </div>
                )}
              </div>

              <div>
                <div className="text-gray-400 uppercase text-[10px] tracking-wider mb-1 font-semibold">
                  Content / Payload
                </div>
                <pre className="p-3 bg-gray-900 text-gray-200 rounded text-[11px] whitespace-pre-wrap max-h-60 overflow-y-auto leading-relaxed">
                  {typeof selectedItem.raw === 'object'
                    ? JSON.stringify(selectedItem.raw, null, 2)
                    : selectedItem.body}
                </pre>
              </div>
            </div>

            <div className="flex justify-end pt-2 border-t border-gray-100">
              <button
                onClick={() => setSelectedItem(null)}
                className="px-3 py-1.5 bg-gray-100 text-gray-700 text-xs font-mono rounded hover:bg-gray-200 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
