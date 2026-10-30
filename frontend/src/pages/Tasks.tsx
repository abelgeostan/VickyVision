import React, { useEffect, useState } from 'react';
import { CheckSquare, Clock, AlertCircle, Play, ChevronRight, X, Terminal } from 'lucide-react';
import { api } from '../services/api';
import { Task } from '../types';
import { Badge } from '../components/common/Badge';

export const Tasks: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTasks = async () => {
    try {
      const data = await api.getTasks();
      setTasks(data);
    } finally {
      setLoading(false);
    }
  };

  const filteredTasks = tasks.filter((t) => {
    if (statusFilter === 'ALL') return true;
    return t.status.toUpperCase() === statusFilter.toUpperCase();
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-gray-200">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-gray-900">
            Tasks
          </h1>
          <p className="text-xs text-gray-500 font-mono mt-0.5">
            Operational work items and autonomous execution pipeline
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="text-gray-400">Filter:</span>
          {['ALL', 'RUNNING', 'COMPLETED', 'PENDING', 'FAILED', 'BLOCKED'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-2.5 py-1 rounded text-[11px] transition-colors ${
                statusFilter === st
                  ? 'bg-gray-900 text-white font-medium'
                  : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Task List */}
      <div className="bg-white border border-gray-200 rounded-lg shadow-2xs overflow-hidden">
        {filteredTasks.length === 0 ? (
          <div className="p-8 text-center text-xs font-mono text-gray-400">
            No tasks found matching filter.
          </div>
        ) : (
          <div className="divide-y divide-gray-100 font-mono text-xs">
            {filteredTasks.map((task) => (
              <div
                key={task.id}
                onClick={() => setSelectedTask(task)}
                className="p-4 hover:bg-gray-50 cursor-pointer transition-colors flex items-center justify-between gap-4"
              >
                <div className="flex items-start gap-3 min-w-0 flex-1">
                  <CheckSquare className="w-4 h-4 text-gray-400 mt-0.5" />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-gray-900 font-sans text-xs truncate">
                        {task.title}
                      </span>
                      <Badge status={task.status} size="sm" />
                    </div>

                    {task.description && (
                      <p className="text-[11px] text-gray-500 line-clamp-1 font-sans">
                        {task.description}
                      </p>
                    )}

                    <div className="flex items-center gap-4 text-[10px] text-gray-400 mt-1.5">
                      <span>Assigned: {task.assigned_to?.toUpperCase() || 'TECHY'}</span>
                      <span>Progress: {task.progress}%</span>
                      {task.project_id && (
                        <span>Project: {task.project_id.slice(0, 8)}...</span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="text-right text-[11px] text-gray-400 shrink-0">
                  <div>{new Date(task.created_at).toLocaleDateString()}</div>
                  <ChevronRight className="w-4 h-4 ml-auto mt-1 text-gray-300" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Task Inspection Modal / Drawer */}
      {selectedTask && (
        <div className="fixed inset-0 bg-black/30 z-40 flex items-center justify-center p-4">
          <div className="bg-white border border-gray-200 rounded-lg max-w-2xl w-full p-5 shadow-lg space-y-4 max-h-[85vh] overflow-y-auto font-mono text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-gray-100">
              <div className="flex items-center gap-2 font-sans font-semibold text-sm text-gray-900">
                <span>{selectedTask.title}</span>
                <Badge status={selectedTask.status} size="sm" />
              </div>
              <button
                onClick={() => setSelectedTask(null)}
                className="text-gray-400 hover:text-gray-700 p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 bg-gray-50 p-3 rounded border border-gray-100">
              <div>
                <span className="text-gray-400">Assigned To:</span>{' '}
                <span className="text-gray-800 font-medium">
                  {selectedTask.assigned_to?.toUpperCase() || 'TECHY'}
                </span>
              </div>
              <div>
                <span className="text-gray-400">Priority:</span>{' '}
                <span className="text-gray-800">{selectedTask.priority}</span>
              </div>
              <div>
                <span className="text-gray-400">Created At:</span>{' '}
                <span className="text-gray-800">
                  {new Date(selectedTask.created_at).toLocaleString()}
                </span>
              </div>
              <div>
                <span className="text-gray-400">Progress:</span>{' '}
                <span className="text-gray-800">{selectedTask.progress}%</span>
              </div>
            </div>

            {selectedTask.description && (
              <div>
                <div className="text-gray-400 uppercase text-[10px] tracking-wider mb-1 font-semibold">
                  Description
                </div>
                <div className="p-3 bg-gray-50 rounded border border-gray-100 font-sans text-gray-700">
                  {selectedTask.description}
                </div>
              </div>
            )}

            {/* Execution Result / Steps from Techy */}
            {selectedTask.result && (
              <div>
                <div className="text-gray-400 uppercase text-[10px] tracking-wider mb-1 font-semibold flex items-center gap-1.5">
                  <Terminal className="w-3.5 h-3.5 text-gray-500" />
                  <span>Techy Execution Output</span>
                </div>
                <pre className="p-3 bg-gray-900 text-gray-200 rounded text-[11px] whitespace-pre-wrap max-h-60 overflow-y-auto leading-relaxed">
                  {JSON.stringify(selectedTask.result, null, 2)}
                </pre>
              </div>
            )}

            {selectedTask.error && (
              <div>
                <div className="text-rose-600 uppercase text-[10px] tracking-wider mb-1 font-semibold">
                  Execution Error
                </div>
                <div className="p-3 bg-rose-50 border border-rose-200 rounded text-rose-800 font-mono text-[11px]">
                  {selectedTask.error}
                </div>
              </div>
            )}

            <div className="flex justify-end pt-2 border-t border-gray-100">
              <button
                onClick={() => setSelectedTask(null)}
                className="px-3 py-1.5 bg-gray-100 text-gray-700 text-xs rounded hover:bg-gray-200 transition-colors"
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
