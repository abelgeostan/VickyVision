import React, { useEffect, useState } from 'react';
import { ScrollText, ShieldCheck, Check, ArrowDown, User, Bot, Compass, ShieldAlert, X } from 'lucide-react';
import { api } from '../services/api';
import { DecisionRecord } from '../types';
import { Badge } from '../components/common/Badge';

export const Decisions: React.FC = () => {
  const [decisions, setDecisions] = useState<DecisionRecord[]>([]);
  const [selectedDecision, setSelectedDecision] = useState<DecisionRecord | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadDecisions();
  }, []);

  const loadDecisions = async () => {
    try {
      const data = await api.getDecisions();
      setDecisions(data);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-gray-200">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-gray-900">
            Decision Records
          </h1>
          <p className="text-xs text-gray-500 font-mono mt-0.5">
            Permanent governance records, architectural rationales & decision provenance
          </p>
        </div>

        <span className="text-xs font-mono text-gray-400">
          {decisions.length} Formal Decisions Recorded
        </span>
      </div>

      {/* Decisions List */}
      <div className="space-y-4">
        {decisions.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-lg p-10 text-center text-xs font-mono text-gray-400">
            No decision records stored yet.
          </div>
        ) : (
          decisions.map((dec) => (
            <div
              key={dec.id}
              onClick={() => setSelectedDecision(dec)}
              className="bg-white border border-gray-200 rounded-lg p-5 shadow-2xs hover:border-gray-300 cursor-pointer transition-colors space-y-3"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-gray-100">
                <div className="flex items-center gap-2">
                  <ScrollText className="w-4 h-4 text-gray-500" />
                  <span className="font-semibold text-xs text-gray-900 font-sans">
                    {dec.title}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge status={dec.category} size="sm" />
                  <Badge status={dec.status} size="sm" />
                </div>
              </div>

              <div className="text-xs text-gray-800 font-sans leading-relaxed">
                <span className="font-mono text-gray-400 font-medium">Resolution:</span> {dec.decision}
              </div>

              {dec.reason && (
                <div className="text-xs text-gray-500 font-sans bg-gray-50 p-2.5 rounded border border-gray-100">
                  <span className="font-mono text-gray-400 text-[11px]">Rationale:</span> {dec.reason}
                </div>
              )}

              <div className="flex flex-wrap items-center justify-between text-[11px] font-mono text-gray-400 pt-2 border-t border-gray-100">
                <div className="flex items-center gap-4">
                  <span>Proposed: {dec.proposed_by.toUpperCase()}</span>
                  {dec.reviewed_by && <span>Reviewed: {dec.reviewed_by.toUpperCase()}</span>}
                  {dec.approved_by && <span>Approved: {dec.approved_by}</span>}
                </div>
                <span>{new Date(dec.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Provenance Inspection Modal (Section 17) */}
      {selectedDecision && (
        <div className="fixed inset-0 bg-black/30 z-40 flex items-center justify-center p-4">
          <div className="bg-white border border-gray-200 rounded-lg max-w-xl w-full p-5 shadow-lg space-y-5 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-gray-100">
              <span className="font-mono font-semibold text-sm text-gray-900">
                Decision Provenance Trail
              </span>
              <button
                onClick={() => setSelectedDecision(null)}
                className="text-gray-400 hover:text-gray-700 p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Visual Provenance Flow (Section 17) */}
            <div className="flex flex-col items-center space-y-2 font-mono text-xs py-2">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded bg-gray-50 border border-gray-200 text-gray-800">
                <User className="w-3.5 h-3.5 text-gray-600" />
                <span>1. User Request (Initiation)</span>
              </div>
              <ArrowDown className="w-3.5 h-3.5 text-gray-300" />

              <div className="flex items-center gap-2 px-3 py-1.5 rounded bg-gray-50 border border-gray-200 text-gray-800">
                <Bot className="w-3.5 h-3.5 text-gray-600" />
                <span>2. PA Triage & Coordination</span>
              </div>
              <ArrowDown className="w-3.5 h-3.5 text-gray-300" />

              <div className="flex items-center gap-2 px-3 py-1.5 rounded bg-gray-50 border border-gray-200 text-gray-800">
                <Compass className="w-3.5 h-3.5 text-gray-600" />
                <span>3. ARCHY Architectural Blueprint</span>
              </div>
              <ArrowDown className="w-3.5 h-3.5 text-gray-300" />

              <div className="flex items-center gap-2 px-3 py-1.5 rounded bg-amber-50 border border-amber-200 text-amber-900">
                <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
                <span>4. ELDER 9-Dimension Review</span>
              </div>
              <ArrowDown className="w-3.5 h-3.5 text-gray-300" />

              <div className="flex items-center gap-2 px-3 py-1.5 rounded bg-emerald-50 border border-emerald-300 text-emerald-900 font-semibold shadow-xs">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                <span>5. Human Authority Approval</span>
              </div>
            </div>

            {/* Details */}
            <div className="space-y-3 text-xs font-sans bg-gray-50 p-4 rounded border border-gray-200">
              <div className="font-semibold text-gray-900 text-sm">
                {selectedDecision.title}
              </div>
              <div className="text-gray-800 leading-relaxed">
                {selectedDecision.decision}
              </div>
              {selectedDecision.review_notes && (
                <div className="text-gray-600 text-xs border-t border-gray-200 pt-2 font-mono">
                  <span className="text-gray-400">Review Notes:</span> {selectedDecision.review_notes}
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2 border-t border-gray-100">
              <button
                onClick={() => setSelectedDecision(null)}
                className="px-3.5 py-1.5 bg-gray-100 text-gray-700 text-xs font-mono rounded hover:bg-gray-200 transition-colors"
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
