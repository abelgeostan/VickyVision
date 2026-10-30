import React from 'react';

interface BadgeProps {
  status: string;
  size?: 'sm' | 'md';
  pulse?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({ status, size = 'sm', pulse = false }) => {
  const norm = status.toUpperCase();

  let dotColor = 'bg-gray-400';
  let textColor = 'text-gray-700';
  let bgColor = 'bg-gray-100 border-gray-200';

  if (['ONLINE', 'COMPLETED', 'APPROVED', 'SUCCESS'].includes(norm)) {
    dotColor = 'bg-emerald-500';
    textColor = 'text-emerald-700';
    bgColor = 'bg-emerald-50 border-emerald-200';
  } else if (['EXECUTING', 'RUNNING', 'WORKING', 'PLANNING'].includes(norm)) {
    dotColor = 'bg-blue-500';
    textColor = 'text-blue-700';
    bgColor = 'bg-blue-50 border-blue-200';
  } else if (['REVIEWING', 'REVIEW', 'WAITING', 'AWAITING_APPROVAL', 'PENDING', 'PROPOSED'].includes(norm)) {
    dotColor = 'bg-amber-500';
    textColor = 'text-amber-700';
    bgColor = 'bg-amber-50 border-amber-200';
  } else if (['FAILED', 'REJECTED', 'BLOCKED', 'ERROR', 'CRITICAL', 'CANCELLED'].includes(norm)) {
    dotColor = 'bg-rose-500';
    textColor = 'text-rose-700';
    bgColor = 'bg-rose-50 border-rose-200';
  }

  const isSmall = size === 'sm';

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-mono uppercase tracking-wider font-medium border rounded-md ${bgColor} ${textColor} ${
        isSmall ? 'text-[10px] px-2 py-0.5' : 'text-xs px-2.5 py-1'
      }`}
    >
      <span className={`rounded-full ${isSmall ? 'w-1.5 h-1.5' : 'w-2 h-2'} ${dotColor} ${pulse ? 'animate-pulse' : ''}`} />
      {status}
    </span>
  );
};
