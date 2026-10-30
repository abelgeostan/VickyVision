import React, { useEffect, useState } from 'react';
import {
  FolderGit2,
  CheckCircle2,
  Clock,
  Compass,
  ShieldCheck,
  Cpu,
  ChevronRight,
  ListTodo,
  FileCheck2,
  History,
  AlertTriangle,
} from 'lucide-react';
import { api } from '../services/api';
import { Project, Task, ProjectTimelineItem, DecisionRecord } from '../types';
import { Badge } from '../components/common/Badge';

export const Projects: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [timeline, setTimeline] = useState<ProjectTimelineItem[]>([]);
  const [decisions, setDecisions] = useState<DecisionRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'tasks' | 'decisions' | 'timeline'>('overview');

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const data = await api.getProjects();
      setProjects(data);
      if (data.length > 0 && !selectedProject) {
        handleSelectProject(data[0]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSelectProject = async (proj: Project) => {
    setSelectedProject(proj);
    setDetailLoading(true);
    try {
      const [tasksRes, timelineRes, decisionsRes] = await Promise.all([
        api.getTasks(proj.id).catch(() => []),
        api.getProjectTimeline(proj.id).catch(() => []),
        api.getDecisions(proj.id).catch(() => []),
      ]);
      setTasks(tasksRes);
      setTimeline(timelineRes);
      setDecisions(decisionsRes);
    } finally {
      setDetailLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="border-b border-gray-200 pb-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-gray-900">
            Projects
          </h1>
          <p className="text-xs text-gray-500 font-mono mt-0.5">
            Architectural blueprints, milestones, and task decomposition
          </p>
        </div>
        <span className="text-xs font-mono text-gray-400">
          {projects.length} Total Projects
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Project List */}
        <div className="space-y-3">
          <div className="text-xs font-mono uppercase tracking-wider text-gray-400 font-medium">
            Project Index
          </div>

          {projects.length === 0 ? (
            <div className="bg-white border border-gray-200 rounded-lg p-6 text-center text-xs font-mono text-gray-400">
              No projects created yet. Send a request to PA to begin!
            </div>
          ) : (
            <div className="space-y-2">
              {projects.map((proj) => {
                const isSelected = selectedProject?.id === proj.id;
                return (
                  <div
                    key={proj.id}
                    onClick={() => handleSelectProject(proj)}
                    className={`p-3.5 rounded-lg border cursor-pointer transition-all bg-white shadow-2xs ${
                      isSelected
                        ? 'border-gray-900 ring-1 ring-gray-900'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-1.5">
                      <div className="font-medium text-xs text-gray-900 line-clamp-1">
                        {proj.name}
                      </div>
                      <Badge status={proj.status} size="sm" />
                    </div>

                    <div className="text-[11px] text-gray-500 line-clamp-2 mb-2 font-sans">
                      {proj.description || 'No description provided.'}
                    </div>

                    <div className="flex items-center justify-between text-[10px] font-mono text-gray-400 pt-2 border-t border-gray-100">
                      <span>By {proj.created_by?.toUpperCase() || 'PA'}</span>
                      <span>{new Date(proj.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right: Selected Project Deep Dive (Section 11) */}
        <div className="lg:col-span-2">
          {selectedProject ? (
            <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-2xs space-y-5">
              {/* Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-gray-100">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h2 className="text-base font-semibold text-gray-900">
                      {selectedProject.name}
                    </h2>
                    <Badge status={selectedProject.status} />
                  </div>
                  <p className="text-xs text-gray-500 font-sans">
                    {selectedProject.description}
                  </p>
                </div>

                <div className="text-[11px] font-mono text-gray-400 text-right shrink-0">
                  <div>ID: {selectedProject.id.slice(0, 13)}...</div>
                  <div>Created: {new Date(selectedProject.created_at).toLocaleString()}</div>
                </div>
              </div>

              {/* Sub-Tabs */}
              <div className="flex items-center gap-2 border-b border-gray-200 pb-2 text-xs font-mono">
                {(['overview', 'tasks', 'decisions', 'timeline'] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-3 py-1 rounded capitalize transition-colors ${
                      activeTab === tab
                        ? 'bg-gray-900 text-white font-medium'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    {tab} {tab === 'tasks' && `(${tasks.length})`}
                  </button>
                ))}
              </div>

              {/* Tab 1: Overview & Architecture */}
              {activeTab === 'overview' && (
                <div className="space-y-4 text-xs font-sans">
                  {/* Proposed Architecture */}
                  <div>
                    <div className="font-mono text-[10px] uppercase tracking-wider text-gray-400 font-semibold mb-1.5">
                      Architectural Blueprint (by ARCHY)
                    </div>
                    <div className="bg-gray-50 p-3.5 rounded border border-gray-200 text-gray-800 leading-relaxed font-mono text-xs whitespace-pre-wrap">
                      {selectedProject.metadata_json?.proposed_architecture ||
                        'Architecture blueprint defined in project milestones.'}
                    </div>
                  </div>

                  {/* Elder Review Findings */}
                  {selectedProject.metadata_json?.elder_review && (
                    <div>
                      <div className="font-mono text-[10px] uppercase tracking-wider text-gray-400 font-semibold mb-1.5 flex items-center gap-1.5">
                        <ShieldCheck className="w-3.5 h-3.5 text-gray-500" />
                        <span>Elder Architectural Evaluation</span>
                      </div>
                      <div className="bg-amber-50/50 p-3.5 rounded border border-amber-200 text-gray-800 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="font-mono font-semibold text-xs text-amber-900">
                            Recommendation: {selectedProject.metadata_json.elder_review.decision}
                          </span>
                        </div>
                        <p className="text-xs text-gray-700">
                          {selectedProject.metadata_json.elder_review.review_summary}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Objectives */}
                  {selectedProject.objectives && (
                    <div>
                      <div className="font-mono text-[10px] uppercase tracking-wider text-gray-400 font-semibold mb-1.5">
                        Project Objectives
                      </div>
                      <ul className="space-y-1 font-mono text-xs">
                        {selectedProject.objectives.map((obj, i) => (
                          <li key={i} className="flex items-center gap-2 text-gray-700">
                            <span className="text-gray-400">•</span>
                            <span>{obj}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Tab 2: Tasks & Milestones */}
              {activeTab === 'tasks' && (
                <div className="space-y-3 font-mono text-xs">
                  {tasks.length === 0 ? (
                    <div className="text-center p-6 text-gray-400">
                      No tasks logged under this project.
                    </div>
                  ) : (
                    tasks.map((task) => (
                      <div
                        key={task.id}
                        className="p-3 rounded border border-gray-200 bg-white hover:border-gray-300 transition-colors shadow-2xs space-y-2"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-gray-900">{task.title}</span>
                          <Badge status={task.status} size="sm" />
                        </div>

                        {task.description && (
                          <p className="text-gray-500 font-sans text-xs">
                            {task.description}
                          </p>
                        )}

                        <div className="flex items-center justify-between text-[10px] text-gray-400 pt-1.5 border-t border-gray-100">
                          <span>Assigned: {task.assigned_to?.toUpperCase() || 'TECHY'}</span>
                          <span>Progress: {task.progress}%</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Tab 3: Decisions */}
              {activeTab === 'decisions' && (
                <div className="space-y-3 font-mono text-xs">
                  {decisions.length === 0 ? (
                    <div className="text-center p-6 text-gray-400">
                      No formal decision records logged for this project.
                    </div>
                  ) : (
                    decisions.map((dec) => (
                      <div
                        key={dec.id}
                        className="p-3.5 rounded border border-gray-200 bg-white space-y-2"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-gray-900">{dec.title}</span>
                          <Badge status={dec.status} size="sm" />
                        </div>
                        <div className="text-gray-700 font-sans text-xs">
                          {dec.decision}
                        </div>
                        {dec.reason && (
                          <div className="text-gray-500 text-[11px] font-sans">
                            <span className="font-mono text-gray-400">Rationale:</span> {dec.reason}
                          </div>
                        )}
                        <div className="flex items-center justify-between text-[10px] text-gray-400 pt-1.5 border-t border-gray-100">
                          <span>Proposed: {dec.proposed_by.toUpperCase()}</span>
                          {dec.approved_by && <span>Approved by: {dec.approved_by}</span>}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Tab 4: Unified Timeline (Section 11) */}
              {activeTab === 'timeline' && (
                <div className="space-y-3 font-mono text-xs">
                  {timeline.length === 0 ? (
                    <div className="text-center p-6 text-gray-400">
                      No timeline events recorded yet.
                    </div>
                  ) : (
                    <div className="space-y-2.5">
                      {timeline.map((item, idx) => (
                        <div
                          key={idx}
                          className="flex items-start gap-3 p-2.5 rounded border border-gray-100 bg-gray-50/50"
                        >
                          <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5" />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between gap-2">
                              <span className="font-medium text-gray-900">{item.title}</span>
                              <span className="text-[10px] text-gray-400">
                                {new Date(item.timestamp).toLocaleTimeString()}
                              </span>
                            </div>
                            <div className="text-[11px] text-gray-500">
                              Source: {item.source} • Type: {item.type}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white border border-gray-200 rounded-lg p-12 text-center text-xs font-mono text-gray-400">
              Select a project from the left panel to inspect architecture, tasks, and unified timeline.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
