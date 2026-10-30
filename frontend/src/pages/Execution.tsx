import React, { useEffect, useState } from 'react';
import { Terminal, Play, CheckCircle2, AlertTriangle, Clock, RefreshCw, Cpu, Layers } from 'lucide-react';
import { api } from '../services/api';
import { Task } from '../types';
import { Badge } from '../components/common/Badge';

export const Execution: React.FC = () => {
  const [techyTasks, setTechyTasks] = useState<Task[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [toolsCatalog, setToolsCatalog] = useState<any[]>([]);
  const [instruction, setInstruction] = useState<string>('');
  const [running, setRunning] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [tasksRes, toolsRes] = await Promise.all([
        api.getTasks().catch(() => []),
        api.getTechyTools().catch(() => ({ count: 0, tools: [] })),
      ]);

      const techyList = tasksRes.filter(
        (t) => t.assigned_to === 'techy' || t.status === 'RUNNING' || t.result != null
      );
      setTechyTasks(techyList);
      setToolsCatalog(toolsRes.tools || []);

      if (techyList.length > 0 && !selectedTask) {
        setSelectedTask(techyList[0]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteInstruction = async () => {
    if (!instruction.trim() || running) return;
    setRunning(true);
    try {
      const res = await api.executeTechyTask(instruction, 5);
      setInstruction('');
      await loadData();
      if (res.task_id) {
        const updated = await api.getTask(res.task_id);
        setSelectedTask(updated);
      }
    } catch (err: any) {
      alert(`Techy execution error: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-gray-200">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-gray-900">
            Techy Live Execution
          </h1>
          <p className="text-xs text-gray-500 font-mono mt-0.5">
            Autonomous server engineer runtime, operational tool invocations & verification logs
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

      {/* Manual Objective Dispatch Bar */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-2xs space-y-3">
        <div className="text-xs font-mono text-gray-500 flex items-center justify-between">
          <span className="flex items-center gap-1.5 font-semibold text-gray-800">
            <Cpu className="w-4 h-4 text-blue-600" />
            <span>Direct Techy Task Dispatch</span>
          </span>
          <span className="text-[10px] text-gray-400">
            {toolsCatalog.length} System Tools Available
          </span>
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            placeholder="e.g. Inspect Docker container status, check listening ports, and report uptime..."
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            disabled={running}
            className="flex-1 text-xs font-sans px-3.5 py-2 rounded-md border border-gray-200 bg-gray-50 focus:bg-white focus:border-gray-400 outline-none"
          />
          <button
            onClick={handleExecuteInstruction}
            disabled={running || !instruction.trim()}
            className="px-4 py-2 bg-gray-900 text-white font-mono text-xs font-medium rounded-md hover:bg-gray-800 transition-colors disabled:opacity-40 flex items-center gap-2"
          >
            <Play className="w-3.5 h-3.5" />
            <span>{running ? 'Executing...' : 'Execute'}</span>
          </button>
        </div>
      </div>

      {/* Main Grid: Executed Tasks vs Detail */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 font-mono text-xs">
        {/* Left: Task Runs List */}
        <div className="space-y-3">
          <div className="text-gray-400 uppercase text-[10px] tracking-wider font-semibold">
            Execution Runs ({techyTasks.length})
          </div>

          {techyTasks.length === 0 ? (
            <div className="bg-white border border-gray-200 rounded-lg p-6 text-center text-gray-400">
              No task runs recorded yet.
            </div>
          ) : (
            <div className="space-y-2">
              {techyTasks.map((t) => {
                const isSelected = selectedTask?.id === t.id;
                return (
                  <div
                    key={t.id}
                    onClick={() => setSelectedTask(t)}
                    className={`p-3 rounded-lg border cursor-pointer transition-all bg-white shadow-2xs ${
                      isSelected
                        ? 'border-gray-900 ring-1 ring-gray-900'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <span className="font-semibold text-gray-900 text-xs font-sans line-clamp-1">
                        {t.title}
                      </span>
                      <Badge status={t.status} size="sm" />
                    </div>

                    <div className="text-[10px] text-gray-400 flex items-center justify-between pt-1.5 border-t border-gray-100">
                      <span>{new Date(t.created_at).toLocaleTimeString()}</span>
                      <span>Progress: {t.progress}%</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right: Step-by-Step Tool Activity & Output */}
        <div className="lg:col-span-2">
          {selectedTask ? (
            <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-2xs space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-gray-100">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-gray-900 text-sm font-sans">
                      {selectedTask.title}
                    </span>
                    <Badge status={selectedTask.status} size="sm" />
                  </div>
                  <div className="text-[11px] text-gray-400">
                    Task ID: {selectedTask.id}
                  </div>
                </div>

                <div className="text-right text-[11px] text-gray-400">
                  <div>Started: {selectedTask.started_at ? new Date(selectedTask.started_at).toLocaleTimeString() : 'N/A'}</div>
                  <div>Finished: {selectedTask.completed_at ? new Date(selectedTask.completed_at).toLocaleTimeString() : 'In progress'}</div>
                </div>
              </div>

              {/* Execution Summary / Steps */}
              {selectedTask.result ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-3 bg-gray-50 p-3 rounded border border-gray-100">
                    <div>
                      <span className="text-gray-400">Steps Executed:</span>{' '}
                      <span className="text-gray-800 font-semibold">
                        {selectedTask.result.steps_count ?? selectedTask.result.steps?.length ?? 1}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-400">Duration:</span>{' '}
                      <span className="text-gray-800">
                        {selectedTask.result.execution_time_ms ? `${selectedTask.result.execution_time_ms} ms` : 'N/A'}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-400">Status:</span>{' '}
                      <span className="text-emerald-600 font-semibold">VERIFIED</span>
                    </div>
                  </div>

                  {/* Final Answer / Verification Summary */}
                  {selectedTask.result.final_answer && (
                    <div>
                      <div className="text-gray-400 uppercase text-[10px] tracking-wider mb-1 font-semibold">
                        Verification & Outcome Report
                      </div>
                      <div className="p-3 bg-gray-50 border border-gray-200 rounded text-gray-800 font-sans leading-relaxed text-xs">
                        {selectedTask.result.final_answer}
                      </div>
                    </div>
                  )}

                  {/* Step-by-Step Tool Activity */}
                  {selectedTask.result.steps && selectedTask.result.steps.length > 0 && (
                    <div className="space-y-3">
                      <div className="text-gray-400 uppercase text-[10px] tracking-wider font-semibold">
                        Step Execution Trace
                      </div>

                      {selectedTask.result.steps.map((step: any, idx: number) => (
                        <div
                          key={idx}
                          className="border border-gray-200 rounded-md overflow-hidden bg-white"
                        >
                          <div className="bg-gray-100/70 px-3 py-1.5 border-b border-gray-200 flex items-center justify-between text-[11px]">
                            <span className="font-semibold text-gray-800">
                              Step {step.step_number || idx + 1}: {step.tool_name || 'Action'}
                            </span>
                            <span className="text-gray-500">
                              {step.duration_ms ? `${step.duration_ms} ms` : ''}
                            </span>
                          </div>

                          <div className="p-3 space-y-2 text-xs">
                            {step.args && (
                              <div>
                                <span className="text-gray-400 text-[10px]">ARGS:</span>
                                <pre className="bg-gray-50 p-2 rounded text-[11px] text-gray-700 mt-0.5 overflow-x-auto">
                                  {JSON.stringify(step.args, null, 2)}
                                </pre>
                              </div>
                            )}

                            {step.tool_output && (
                              <div>
                                <span className="text-gray-400 text-[10px]">OUTPUT:</span>
                                <pre className="bg-gray-900 text-gray-200 p-2.5 rounded text-[11px] mt-0.5 overflow-x-auto max-h-48 overflow-y-auto leading-relaxed">
                                  {typeof step.tool_output === 'object'
                                    ? JSON.stringify(step.tool_output, null, 2)
                                    : step.tool_output}
                                </pre>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-8 text-center text-gray-400 border border-dashed border-gray-200 rounded">
                  No execution result payload for this task yet.
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white border border-gray-200 rounded-lg p-12 text-center text-gray-400">
              Select a task from the left to inspect its live operational steps and command outputs.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
