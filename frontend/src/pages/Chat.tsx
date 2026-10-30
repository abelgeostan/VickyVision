import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  Bot,
  User,
  ShieldCheck,
  Check,
  X,
  RotateCw,
  Compass,
  Cpu,
  Layers,
  AlertCircle,
} from 'lucide-react';
import { api } from '../services/api';
import { eventStream } from '../services/events';
import { Message, PAResponse } from '../types';
import { Badge } from '../components/common/Badge';

interface ChatEntry {
  id: string;
  sender: 'user' | 'pa' | 'archy' | 'elder' | 'techy';
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
  approvalId?: string;
  actionTaken?: string;
  intent?: string;
  isDelegation?: boolean;
}

export const Chat: React.FC = () => {
  const [messages, setMessages] = useState<ChatEntry[]>([]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [delegationStage, setDelegationStage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load message history from backend on mount
  useEffect(() => {
    loadHistory();

    // Listen to real-time events to reflect background agent activities in chat
    const unsub = eventStream.subscribe((evt) => {
      if (evt.event_type === 'archy.plan_created') {
        setDelegationStage('Archy completed architectural blueprint');
      } else if (evt.event_type === 'elder.review_completed') {
        setDelegationStage('Elder completed architectural evaluation');
      } else if (evt.event_type.startsWith('techy.execution.')) {
        setDelegationStage('Techy executing tasks on VICKY server...');
      }
    });

    return () => unsub();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, delegationStage]);

  const loadHistory = async () => {
    try {
      const msgs = await api.getMessages({ limit: 50 });
      // Filter or sort messages between user and pa
      const userPaMsgs = msgs
        .filter(
          (m) =>
            (m.sender_id === 'user' && m.receiver_id === 'pa') ||
            (m.sender_id === 'pa' && m.receiver_id === 'user')
        )
        .reverse()
        .map((m) => ({
          id: m.id,
          sender: m.sender_id as 'user' | 'pa',
          content: m.content,
          timestamp: m.created_at,
          metadata: m.metadata_json,
          approvalId: m.metadata_json?.approval_id,
          actionTaken: m.metadata_json?.action_taken,
          intent: m.metadata_json?.intent,
        }));

      if (userPaMsgs.length > 0) {
        setMessages(userPaMsgs);
      } else {
        // Welcome message if fresh
        setMessages([
          {
            id: 'welcome',
            sender: 'pa',
            content:
              "Hello! I am PA, your Personal Assistant and primary liaison to VICKY OS. You can describe projects, technical goals, or ask questions about the server and organization. How can I assist you today?",
            timestamp: new Date().toISOString(),
          },
        ]);
      }
    } catch (err) {
      console.error('Could not load chat history:', err);
    }
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    setError(null);
    setInput('');
    setLoading(true);
    setDelegationStage('PA analyzing request...');

    // Optimistically add user message
    const tempUserId = `user-${Date.now()}`;
    const userEntry: ChatEntry = {
      id: tempUserId,
      sender: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userEntry]);

    try {
      // Real API call to PA
      const res: PAResponse = await api.chatWithPA(text);

      const paEntry: ChatEntry = {
        id: `pa-${Date.now()}`,
        sender: 'pa',
        content: res.message,
        timestamp: new Date().toISOString(),
        approvalId: res.approval_id || undefined,
        actionTaken: res.action_taken,
        intent: res.intent,
      };

      setMessages((prev) => [...prev, paEntry]);
    } catch (err: any) {
      setError(err.message || 'Failed to communicate with PA.');
    } finally {
      setLoading(false);
      setDelegationStage(null);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleDecision = async (
    approvalId: string,
    decision: 'APPROVE' | 'REJECT' | 'REQUEST_CHANGES'
  ) => {
    setActionLoading(approvalId);
    setDelegationStage(`Submitting ${decision} decision to organization...`);
    try {
      const res = await api.submitApprovalDecision(approvalId, decision);
      // Append PA update after human decision
      const updateEntry: ChatEntry = {
        id: `pa-decision-${Date.now()}`,
        sender: 'pa',
        content: res.message,
        timestamp: new Date().toISOString(),
        actionTaken: res.action_taken,
        intent: res.intent,
      };
      setMessages((prev) => [...prev, updateEntry]);
    } catch (err: any) {
      alert(`Approval decision failed: ${err.message}`);
    } finally {
      setActionLoading(null);
      setDelegationStage(null);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-6.5rem)] max-w-4xl mx-auto bg-white border border-gray-200 rounded-lg shadow-xs overflow-hidden">
      {/* Chat Header */}
      <div className="h-13 px-4 border-b border-gray-200 flex items-center justify-between bg-gray-50/50">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-md bg-gray-900 text-white flex items-center justify-center font-mono text-xs font-semibold">
            PA
          </div>
          <div>
            <div className="font-medium text-xs text-gray-900">Personal Assistant</div>
            <div className="text-[10px] text-gray-500 font-mono">
              Primary Human Liaison • Organization Orchestrator
            </div>
          </div>
        </div>

        <button
          onClick={loadHistory}
          className="text-gray-400 hover:text-gray-700 p-1.5 rounded hover:bg-gray-100 transition-colors"
          title="Refresh messages"
        >
          <RotateCw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Message Feed */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';
          const time = new Date(msg.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          });

          return (
            <div
              key={msg.id}
              className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
            >
              {/* Avatar */}
              <div
                className={`w-7 h-7 rounded-md shrink-0 flex items-center justify-center text-xs font-mono font-medium ${
                  isUser
                    ? 'bg-gray-100 text-gray-700 border border-gray-200'
                    : 'bg-gray-900 text-white'
                }`}
              >
                {isUser ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
              </div>

              {/* Message Content Bubble */}
              <div
                className={`max-w-[82%] sm:max-w-[75%] rounded-lg p-3 text-xs leading-relaxed ${
                  isUser
                    ? 'bg-gray-900 text-white'
                    : 'bg-gray-50 border border-gray-200 text-gray-800'
                }`}
              >
                {/* Header info */}
                <div
                  className={`flex items-center gap-2 mb-1.5 text-[10px] font-mono ${
                    isUser ? 'text-gray-400 justify-end' : 'text-gray-400'
                  }`}
                >
                  <span className="font-semibold text-gray-500">
                    {isUser ? 'YOU' : 'PA'}
                  </span>
                  <span>{time}</span>
                  {msg.intent && !isUser && (
                    <span className="px-1.5 py-0.2 rounded bg-gray-200/70 text-gray-600">
                      {msg.intent}
                    </span>
                  )}
                </div>

                {/* Text Body with simple markdown linebreaks */}
                <div className="whitespace-pre-wrap font-sans text-xs">
                  {msg.content}
                </div>

                {/* Inline Action Indicator if present */}
                {msg.actionTaken && !isUser && (
                  <div className="mt-2 pt-2 border-t border-gray-200/60 font-mono text-[10px] text-gray-500 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                    <span>{msg.actionTaken}</span>
                  </div>
                )}

                {/* Inline Human Approval Card if pending approval attached (Section 8) */}
                {msg.approvalId && !isUser && (
                  <div className="mt-3 p-3 bg-white rounded border border-amber-200 shadow-2xs space-y-2.5 text-xs text-gray-800">
                    <div className="flex items-center justify-between font-mono text-[11px] text-amber-900 font-medium">
                      <span className="flex items-center gap-1.5">
                        <ShieldCheck className="w-3.5 h-3.5 text-amber-600" />
                        <span>Executive Approval Required</span>
                      </span>
                      <span className="text-[10px] text-gray-400">#authority</span>
                    </div>

                    <p className="text-[11px] text-gray-600">
                      Archy and Elder have prepared this project proposal. Do you authorize Techy to execute this implementation on the server?
                    </p>

                    <div className="flex flex-wrap items-center gap-2 pt-1 font-mono text-xs">
                      <button
                        disabled={actionLoading === msg.approvalId}
                        onClick={() => handleDecision(msg.approvalId!, 'APPROVE')}
                        className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-600 text-white rounded hover:bg-emerald-700 transition-colors disabled:opacity-50"
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>Approve</span>
                      </button>
                      <button
                        disabled={actionLoading === msg.approvalId}
                        onClick={() => handleDecision(msg.approvalId!, 'REQUEST_CHANGES')}
                        className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-600 text-white rounded hover:bg-amber-700 transition-colors disabled:opacity-50"
                      >
                        <span>Request Changes</span>
                      </button>
                      <button
                        disabled={actionLoading === msg.approvalId}
                        onClick={() => handleDecision(msg.approvalId!, 'REJECT')}
                        className="inline-flex items-center gap-1.5 px-3 py-1 bg-rose-600 text-white rounded hover:bg-rose-700 transition-colors disabled:opacity-50"
                      >
                        <X className="w-3.5 h-3.5" />
                        <span>Reject</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Real-time Organizational Activity Indicator (Section 8) */}
        {delegationStage && (
          <div className="flex items-center gap-2.5 p-2.5 rounded border border-blue-100 bg-blue-50/50 text-blue-900 font-mono text-xs animate-pulse max-w-md">
            <span className="w-2 h-2 rounded-full bg-blue-500" />
            <span className="font-medium">{delegationStage}</span>
          </div>
        )}

        {/* Error notification */}
        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded text-rose-800 text-xs flex items-center gap-2 font-mono">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
            <span>{error}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="p-3 border-t border-gray-200 bg-white">
        <div className="flex items-end gap-2 bg-gray-50 border border-gray-300 rounded-lg p-2 focus-within:border-gray-500 transition-colors">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
            placeholder="Tell PA what you want to build or ask about the system... (Enter to send, Shift+Enter for newline)"
            rows={2}
            className="flex-1 bg-transparent border-0 outline-none resize-none text-xs text-gray-900 placeholder:text-gray-400 leading-relaxed font-sans"
          />

          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="p-2 rounded-md bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-40 transition-colors shrink-0"
            aria-label="Send message"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>

        <div className="flex items-center justify-between text-[10px] font-mono text-gray-400 mt-1.5 px-1">
          <span>PA coordinates Archy, Elder & Techy</span>
          <span>Shift + Enter for new line</span>
        </div>
      </div>
    </div>
  );
};
