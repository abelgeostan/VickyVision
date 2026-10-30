import React, { useEffect, useState } from 'react';
import { Database, Search, Filter, Bookmark, Sparkles, Clock } from 'lucide-react';
import { api } from '../services/api';
import { MemoryItem } from '../types';
import { Badge } from '../components/common/Badge';

export const Memory: React.FC = () => {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadMemories();
  }, []);

  const loadMemories = async () => {
    try {
      const data = await api.getMemories(undefined, 100);
      setMemories(data);
    } finally {
      setLoading(false);
    }
  };

  const categories = [
    'ALL',
    'USER_PREFERENCE',
    'PROJECT_FACT',
    'ARCHITECTURAL_DECISION',
    'SERVER_FACT',
    'LESSON_LEARNED',
  ];

  const filteredMemories = memories.filter((m) => {
    if (categoryFilter !== 'ALL' && m.type.toUpperCase() !== categoryFilter.toUpperCase()) {
      return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        m.content.toLowerCase().includes(q) ||
        m.agent_id.toLowerCase().includes(q) ||
        m.type.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-gray-200">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-gray-900">
            Organizational Memory
          </h1>
          <p className="text-xs text-gray-500 font-mono mt-0.5">
            Persistent knowledge base across user preferences, architectures, server facts & operational lessons
          </p>
        </div>

        <span className="text-xs font-mono text-gray-400">
          {memories.length} Stored Memory Facts
        </span>
      </div>

      {/* Search & Category Filter Controls */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-2xs space-y-3 font-mono text-xs">
        <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-md px-3 py-1.5 focus-within:border-gray-400 transition-colors">
          <Search className="w-3.5 h-3.5 text-gray-400" />
          <input
            type="text"
            placeholder="Search organizational memories..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 bg-transparent border-0 outline-none text-xs text-gray-800 placeholder:text-gray-400 font-sans"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="text-gray-400 text-[11px]">Category:</span>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              className={`px-2.5 py-1 rounded text-[11px] transition-colors ${
                categoryFilter === cat
                  ? 'bg-gray-900 text-white font-medium'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {cat.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Memory Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredMemories.length === 0 ? (
          <div className="col-span-2 bg-white border border-gray-200 rounded-lg p-10 text-center text-xs font-mono text-gray-400">
            No memories found matching filter.
          </div>
        ) : (
          filteredMemories.map((m) => (
            <div
              key={m.id}
              className="bg-white border border-gray-200 rounded-lg p-4 shadow-2xs space-y-3 hover:border-gray-300 transition-colors"
            >
              <div className="flex items-start justify-between gap-2">
                <Badge status={m.type} size="sm" />
                <span className="text-[10px] font-mono text-gray-400">
                  Importance: {m.importance}/10
                </span>
              </div>

              <p className="text-xs text-gray-800 font-sans leading-relaxed">
                {m.content}
              </p>

              <div className="flex items-center justify-between text-[10px] font-mono text-gray-400 pt-2 border-t border-gray-100">
                <span>Recorded by: {m.agent_id.toUpperCase()}</span>
                <span>{new Date(m.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
