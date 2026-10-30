import React, { useEffect, useState } from 'react';
import { Bot, Compass, ShieldAlert, Cpu, Sparkles, AlertCircle } from 'lucide-react';
import { api } from '../services/api';
import { Agent, Task } from '../types';
import { Badge } from '../components/common/Badge';

export const Agents: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [agentsRes, tasksRes] = await Promise.all([
        api.getAgents().catch(() => []),
        api.getTasks().catch(() => []),
      ]);
      setAgents(agentsRes);
      setTasks(tasksRes);
      if (agentsRes.length > 0 && !selectedAgent) {
        setSelectedAgent(agentsRes[0]);
      }
    } finally {
      setLoading(false);
    }
  };

  const getAgentIcon = (id: string) => {
    switch (id.toLowerCase()) {
      case 'pa':
        return <Bot className="w-5 h-5 text-gray-700" />;
      case 'archy':
        return <Compass className="w-5 h-5 text-gray-700" />;
      case 'elder':
        return <ShieldAlert className="w-5 h-5 text-gray-700" />;
      case 'techy':
        return <Cpu className="w-5 h-5 text-gray-700" />;
      default:
        return <Bot className="w-5 h-5 text-gray-700" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-xl font-semibold tracking-tight text-gray-900">
          Organization Agents
        </h1>
        <p className="text-xs text-gray-500 font-mono mt-0.5">
          Identities, roles, boundaries, and active models
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Agent Cards */}
        {agents.map((agent) => {
          const isSelected = selectedAgent?.id === agent.id;
          const assignedTasks = tasks.filter((t) => t.assigned_to === agent.id);
          const completedCount = assignedTasks.filter((t) => t.status === 'COMPLETED').length;

          return (
            <div
              key={agent.id}
              onClick={() => setSelectedAgent(agent)}
              className={`p-4 rounded-lg border cursor-pointer transition-all bg-white shadow-2xs ${
                isSelected
                  ? 'border-gray-900 ring-1 ring-gray-900'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="p-2 rounded-md bg-gray-50 border border-gray-200">
                  {getAgentIcon(agent.id)}
                </div>
                <Badge status={agent.status || 'ONLINE'} size="sm" />
              </div>

              <div className="font-mono font-semibold text-gray-900 text-sm">
                {agent.name.toUpperCase()}
              </div>
              <div className="text-xs text-gray-500 font-medium mb-3">
                {agent.role}
              </div>

              <div className="space-y-1.5 text-[11px] font-mono text-gray-400 pt-3 border-t border-gray-100">
                <div className="flex justify-between">
                  <span>Model:</span>
                  <span className="text-gray-700">{agent.model_name || 'gemma3:4b'}</span>
                </div>
                <div className="flex justify-between">
                  <span>Completed Tasks:</span>
                  <span className="text-gray-700">{completedCount}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Agent Deep Dive */}
      {selectedAgent && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-6 shadow-2xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-gray-100">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-gray-100 border border-gray-200">
                {getAgentIcon(selectedAgent.id)}
              </div>
              <div>
                <h2 className="text-base font-semibold text-gray-900 font-mono">
                  {selectedAgent.name.toUpperCase()} ({selectedAgent.id})
                </h2>
                <p className="text-xs text-gray-500">{selectedAgent.role}</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-gray-400">Model:</span>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-gray-100 border border-gray-200 text-gray-700 font-medium">
                {selectedAgent.model_name || 'gemma3:4b'}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
            {/* Responsibilities & Description */}
            <div className="space-y-3">
              <div className="font-mono uppercase text-gray-400 text-[10px] tracking-wider font-semibold">
                Responsibilities & Purpose
              </div>
              <p className="text-gray-700 leading-relaxed font-sans bg-gray-50 p-3.5 rounded border border-gray-100">
                {selectedAgent.description || 'No description provided.'}
              </p>

              {selectedAgent.personality && (
                <div>
                  <div className="font-mono uppercase text-gray-400 text-[10px] tracking-wider font-semibold mb-1">
                    Persona & Tone
                  </div>
                  <p className="text-gray-600 italic bg-gray-50 p-3 rounded border border-gray-100 font-sans">
                    "{selectedAgent.personality}"
                  </p>
                </div>
              )}
            </div>

            {/* Core Objectives */}
            <div className="space-y-3">
              <div className="font-mono uppercase text-gray-400 text-[10px] tracking-wider font-semibold">
                Core Objectives & Protocol
              </div>
              {selectedAgent.objectives && selectedAgent.objectives.length > 0 ? (
                <ul className="space-y-1.5 font-mono text-xs">
                  {selectedAgent.objectives.map((obj, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-2 p-2 rounded bg-gray-50 border border-gray-100 text-gray-700"
                    >
                      <span className="text-gray-400">•</span>
                      <span>{obj}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="text-gray-400 font-mono text-xs">No explicit objectives configured.</div>
              )}
            </div>
          </div>

          {/* System Prompt (Sanitized / Excerpt) */}
          {selectedAgent.system_prompt && (
            <div className="space-y-2 pt-4 border-t border-gray-100">
              <div className="font-mono uppercase text-gray-400 text-[10px] tracking-wider font-semibold">
                System Prompt Directive
              </div>
              <pre className="p-3 bg-gray-900 text-gray-200 rounded text-[11px] font-mono whitespace-pre-wrap max-h-48 overflow-y-auto leading-relaxed">
                {selectedAgent.system_prompt}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
