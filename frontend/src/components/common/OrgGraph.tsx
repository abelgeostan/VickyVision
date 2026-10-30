import React from 'react';
import { User, Bot, Compass, ShieldAlert, Cpu } from 'lucide-react';

interface OrgGraphProps {
  activeAgent?: string;
}

export const OrgGraph: React.FC<OrgGraphProps> = ({ activeAgent }) => {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5">
      <div className="text-xs font-mono uppercase tracking-wider text-gray-500 mb-4 flex items-center justify-between">
        <span>Organizational Hierarchy</span>
        <span className="text-[11px] text-gray-400">Authority Flow</span>
      </div>

      <div className="flex flex-col items-center select-none text-xs">
        {/* User / Human Authority */}
        <div className="flex flex-col items-center">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-gray-300 bg-gray-50 font-mono text-gray-800 shadow-xs">
            <User className="w-3.5 h-3.5 text-gray-600" />
            <span className="font-semibold">YOU</span>
            <span className="text-[10px] text-gray-400">(Authority)</span>
          </div>
          <div className="w-px h-5 bg-gray-300 my-0.5" />
          <div className="w-0 h-0 border-l-[3px] border-l-transparent border-r-[3px] border-r-transparent border-t-[5px] border-t-gray-400 mb-1" />
        </div>

        {/* PA */}
        <div className="flex flex-col items-center w-full max-w-md">
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md border font-mono transition-colors shadow-xs ${
              activeAgent === 'pa'
                ? 'border-blue-500 bg-blue-50 text-blue-900 ring-1 ring-blue-500'
                : 'border-gray-200 bg-white text-gray-800'
            }`}
          >
            <Bot className="w-3.5 h-3.5 text-gray-600" />
            <span className="font-semibold">PA</span>
            <span className="text-[10px] text-gray-400">Personal Assistant (Interface)</span>
          </div>

          {/* Connector down to specialized agents */}
          <div className="w-px h-5 bg-gray-300 my-0.5" />

          {/* Branch bar */}
          <div className="w-3/4 h-px bg-gray-300 relative flex justify-between">
            <div className="w-px h-4 bg-gray-300 absolute left-0 top-0" />
            <div className="w-px h-4 bg-gray-300 absolute right-0 top-0" />
          </div>

          {/* Specialized Agents Row */}
          <div className="flex justify-between w-full mt-4 gap-3">
            {/* ARCHY & ELDER column */}
            <div className="flex-1 flex flex-col items-center p-2 rounded-md border border-dashed border-gray-200 bg-gray-50/50">
              <div className="text-[10px] font-mono text-gray-400 uppercase tracking-widest mb-1.5">Architecture & Review</div>
              <div className="flex flex-col items-center gap-1.5 w-full">
                <div
                  className={`flex items-center justify-between w-full px-2.5 py-1 rounded border font-mono text-[11px] ${
                    activeAgent === 'archy'
                      ? 'border-blue-500 bg-blue-50 text-blue-900'
                      : 'border-gray-200 bg-white text-gray-700'
                  }`}
                >
                  <span className="flex items-center gap-1.5">
                    <Compass className="w-3 h-3 text-gray-500" />
                    <span className="font-medium">ARCHY</span>
                  </span>
                  <span className="text-[9px] text-gray-400">Vision</span>
                </div>

                <div className="text-[9px] text-gray-400 font-mono flex items-center gap-1">
                  <span>↕</span> <span>Review Loop</span>
                </div>

                <div
                  className={`flex items-center justify-between w-full px-2.5 py-1 rounded border font-mono text-[11px] ${
                    activeAgent === 'elder'
                      ? 'border-blue-500 bg-blue-50 text-blue-900'
                      : 'border-gray-200 bg-white text-gray-700'
                  }`}
                >
                  <span className="flex items-center gap-1.5">
                    <ShieldAlert className="w-3 h-3 text-gray-500" />
                    <span className="font-medium">ELDER</span>
                  </span>
                  <span className="text-[9px] text-gray-400">Wisdom</span>
                </div>
              </div>
            </div>

            {/* TECHY column */}
            <div className="flex-1 flex flex-col items-center p-2 rounded-md border border-dashed border-gray-200 bg-gray-50/50">
              <div className="text-[10px] font-mono text-gray-400 uppercase tracking-widest mb-1.5">Execution Runtime</div>
              <div
                className={`flex items-center justify-between w-full px-2.5 py-3 rounded border font-mono text-[11px] ${
                  activeAgent === 'techy'
                    ? 'border-blue-500 bg-blue-50 text-blue-900'
                    : 'border-gray-200 bg-white text-gray-700'
                }`}
              >
                <span className="flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-gray-500" />
                  <span className="font-medium">TECHY</span>
                </span>
                <span className="text-[9px] text-gray-400">Hands (Server)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
