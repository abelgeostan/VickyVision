import React, { useEffect, useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  MessageSquare,
  Users,
  GitBranch,
  FolderGit2,
  CheckSquare,
  FileCheck2,
  Terminal,
  Server,
  Database,
  ScrollText,
  Radio,
  Menu,
  X,
} from 'lucide-react';
import { eventStream } from '../../services/events';
import { api } from '../../services/api';

export const Shell: React.FC = () => {
  const [streamStatus, setStreamStatus] = useState<'connected' | 'connecting' | 'disconnected'>('disconnected');
  const [systemOnline, setSystemOnline] = useState<boolean>(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);
  const location = useLocation();

  useEffect(() => {
    // Subscribe to SSE real-time connection status
    const unsub = eventStream.subscribeStatus((status) => {
      setStreamStatus(status);
    });

    // Check backend health
    api
      .checkHealth()
      .then(() => setSystemOnline(true))
      .catch(() => setSystemOnline(false));

    return () => unsub();
  }, []);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  const navSections = [
    {
      title: 'COMMAND CENTER',
      items: [
        { label: 'Command Center', path: '/', icon: LayoutDashboard },
      ],
    },
    {
      title: 'PRIMARY INTERFACE',
      items: [
        { label: 'PA Chat', path: '/chat', icon: MessageSquare },
      ],
    },
    {
      title: 'ORGANIZATION',
      items: [
        { label: 'Agents', path: '/agents', icon: Users },
        { label: 'Conversations', path: '/conversations', icon: GitBranch },
      ],
    },
    {
      title: 'WORK',
      items: [
        { label: 'Projects', path: '/projects', icon: FolderGit2 },
        { label: 'Tasks', path: '/tasks', icon: CheckSquare },
        { label: 'Approvals', path: '/approvals', icon: FileCheck2 },
      ],
    },
    {
      title: 'OPERATIONS',
      items: [
        { label: 'Techy Live', path: '/execution', icon: Terminal },
        { label: 'Server', path: '/server', icon: Server },
      ],
    },
    {
      title: 'KNOWLEDGE',
      items: [
        { label: 'Memory', path: '/memory', icon: Database },
        { label: 'Decisions', path: '/decisions', icon: ScrollText },
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-[#f9fafb] text-[#111827] flex flex-col font-sans">
      {/* Top Header */}
      <header className="h-13 bg-white border-b border-gray-200 px-4 md:px-6 flex items-center justify-between sticky top-0 z-30">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-1.5 text-gray-500 hover:text-gray-900 rounded-md hover:bg-gray-100"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

          <div className="flex items-center gap-2">
            <span className="font-mono text-sm tracking-wider font-semibold text-gray-900">
              VICKY OS
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded border border-gray-200 text-gray-400 bg-gray-50">
              v1.0
            </span>
          </div>
        </div>

        {/* Global Status Badges */}
        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="hidden sm:flex items-center gap-1.5 text-gray-500">
            <Radio className={`w-3.5 h-3.5 ${streamStatus === 'connected' ? 'text-emerald-500 animate-pulse' : 'text-amber-500'}`} />
            <span className="text-[11px] text-gray-400">Event Stream:</span>
            <span
              className={`text-[11px] capitalize ${
                streamStatus === 'connected'
                  ? 'text-emerald-600 font-medium'
                  : 'text-amber-600'
              }`}
            >
              {streamStatus}
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            <span
              className={`w-2 h-2 rounded-full ${
                systemOnline ? 'bg-emerald-500' : 'bg-rose-500'
              }`}
            />
            <span className="text-[11px] font-medium text-gray-700">
              {systemOnline ? 'System Online' : 'Offline'}
            </span>
          </div>
        </div>
      </header>

      <div className="flex flex-1 relative overflow-hidden">
        {/* Sidebar Navigation */}
        <aside
          className={`${
            mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
          } md:translate-x-0 transition-transform duration-200 ease-in-out fixed md:static inset-y-0 left-0 z-20 w-60 bg-white border-r border-gray-200 flex flex-col pt-13 md:pt-0 overflow-y-auto`}
        >
          <div className="p-3 space-y-5">
            {navSections.map((sec) => (
              <div key={sec.title}>
                <div className="text-[10px] font-mono tracking-wider uppercase text-gray-400 px-2.5 mb-1.5 font-medium">
                  {sec.title}
                </div>
                <div className="space-y-0.5">
                  {sec.items.map((item) => {
                    const Icon = item.icon;
                    return (
                      <NavLink
                        key={item.path}
                        to={item.path}
                        end={item.path === '/'}
                        className={({ isActive }) =>
                          `flex items-center gap-2.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors ${
                            isActive
                              ? 'bg-gray-100 text-gray-900 font-semibold'
                              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                          }`
                        }
                      >
                        <Icon className="w-4 h-4 text-gray-500" />
                        <span>{item.label}</span>
                      </NavLink>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-auto p-3 border-t border-gray-100 text-[11px] font-mono text-gray-400 flex items-center justify-between">
            <span>Autonomous AI Org</span>
            <span>Self-Hosted</span>
          </div>
        </aside>

        {/* Backdrop for mobile */}
        {mobileMenuOpen && (
          <div
            onClick={() => setMobileMenuOpen(false)}
            className="md:hidden fixed inset-0 bg-black/20 z-10"
          />
        )}

        {/* Main View Area */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
