import React, { useEffect, useState } from 'react';
import { ShieldCheck, Check, X, RotateCcw, AlertTriangle, Clock } from 'lucide-react';
import { api } from '../services/api';
import { ApprovalRequest } from '../types';
import { Badge } from '../components/common/Badge';

export const Approvals: React.FC = () => {
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [filter, setFilter] = useState<'ALL' | 'PENDING' | 'DECIDED'>('PENDING');
  const [loading, setLoading] = useState<boolean>(true);
  const [submittingId, setSubmittingId] = useState<string | null>(null);
  const [notesInput, setNotesInput] = useState<Record<string, string>>({});

  useEffect(() => {
    loadApprovals();
  }, []);

  const loadApprovals = async () => {
    try {
      const data = await api.getApprovals();
      setApprovals(data);
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async (
    approvalId: string,
    decision: 'APPROVE' | 'REJECT' | 'REQUEST_CHANGES'
  ) => {
    setSubmittingId(approvalId);
    try {
      const notes = notesInput[approvalId] || undefined;
      await api.submitApprovalDecision(approvalId, decision, notes);
      await loadApprovals();
    } catch (err: any) {
      alert(`Decision submission error: ${err.message}`);
    } finally {
      setSubmittingId(null);
    }
  };

  const filteredApprovals = approvals.filter((a) => {
    if (filter === 'PENDING') return a.status === 'PENDING';
    if (filter === 'DECIDED') return a.status !== 'PENDING';
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-gray-200">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-gray-900">
            Human Approvals
          </h1>
          <p className="text-xs text-gray-500 font-mono mt-0.5">
            Executive authority gate for project proposals and impactful operations
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          {(['PENDING', 'DECIDED', 'ALL'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 rounded text-[11px] transition-colors ${
                filter === f
                  ? 'bg-gray-900 text-white font-medium'
                  : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              {f} ({approvals.filter((a) => (f === 'PENDING' ? a.status === 'PENDING' : f === 'DECIDED' ? a.status !== 'PENDING' : true)).length})
            </button>
          ))}
        </div>
      </div>

      {/* Approvals List */}
      <div className="space-y-4">
        {filteredApprovals.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-lg p-10 text-center text-xs font-mono text-gray-400">
            No approval requests found in this category.
          </div>
        ) : (
          filteredApprovals.map((req) => {
            const isPending = req.status === 'PENDING';
            const isSubmitting = submittingId === req.id;

            return (
              <div
                key={req.id}
                className={`bg-white border rounded-lg p-5 shadow-2xs space-y-4 transition-all ${
                  isPending ? 'border-amber-300 ring-1 ring-amber-200' : 'border-gray-200'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-gray-100">
                  <div className="flex items-center gap-2.5">
                    <ShieldCheck className={`w-4 h-4 ${isPending ? 'text-amber-600' : 'text-gray-400'}`} />
                    <span className="font-mono font-semibold text-sm text-gray-900">
                      {req.action}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge status={`RISK: ${req.risk_level}`} size="sm" />
                    <Badge status={req.status} size="sm" />
                  </div>
                </div>

                <div className="space-y-2 text-xs">
                  {req.reason && (
                    <div className="text-gray-700 leading-relaxed font-sans bg-gray-50 p-3 rounded border border-gray-100">
                      {req.reason}
                    </div>
                  )}

                  <div className="flex flex-wrap items-center gap-4 text-[11px] font-mono text-gray-400">
                    <span>Requested by: {req.requesting_agent_id.toUpperCase()}</span>
                    <span>Created: {new Date(req.created_at).toLocaleString()}</span>
                    {req.project_id && <span>Project ID: {req.project_id.slice(0, 12)}...</span>}
                    {req.approved_by && <span>Decided by: {req.approved_by}</span>}
                  </div>
                </div>

                {/* Actions for Pending Requests */}
                {isPending && (
                  <div className="pt-3 border-t border-gray-100 space-y-3">
                    <input
                      type="text"
                      placeholder="Optional notes or feedback for Archy / Techy..."
                      value={notesInput[req.id] || ''}
                      onChange={(e) =>
                        setNotesInput((prev) => ({ ...prev, [req.id]: e.target.value }))
                      }
                      className="w-full text-xs font-sans px-3 py-1.5 rounded border border-gray-200 bg-gray-50 focus:bg-white focus:border-gray-400 outline-none"
                    />

                    <div className="flex items-center gap-2 font-mono text-xs">
                      <button
                        disabled={isSubmitting}
                        onClick={() => handleDecision(req.id, 'APPROVE')}
                        className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-emerald-600 text-white rounded font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50"
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>{isSubmitting ? 'Processing...' : 'Approve Execution'}</span>
                      </button>

                      <button
                        disabled={isSubmitting}
                        onClick={() => handleDecision(req.id, 'REQUEST_CHANGES')}
                        className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-amber-600 text-white rounded font-medium hover:bg-amber-700 transition-colors disabled:opacity-50"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        <span>Request Changes</span>
                      </button>

                      <button
                        disabled={isSubmitting}
                        onClick={() => handleDecision(req.id, 'REJECT')}
                        className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-rose-600 text-white rounded font-medium hover:bg-rose-700 transition-colors disabled:opacity-50"
                      >
                        <X className="w-3.5 h-3.5" />
                        <span>Reject</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
