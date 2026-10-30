import React from 'react';
import { SystemEvent } from '../../types';
import { Badge } from './Badge';

interface LiveActivityStreamProps {
  events: SystemEvent[];
  maxItems?: number;
  showFilter?: boolean;
}

export const LiveActivityStream: React.FC<LiveActivityStreamProps> = ({
  events,
  maxItems = 10,
}) => {
  const displayEvents = events.slice(0, maxItems);

  if (displayEvents.length === 0) {
    return (
      <div className="text-xs font-mono text-gray-400 p-4 border border-dashed border-gray-200 rounded text-center">
        No recent system events logged yet.
      </div>
    );
  }

  return (
    <div className="space-y-3 font-mono text-xs">
      {displayEvents.map((evt) => {
        const timeStr = evt.created_at
          ? new Date(evt.created_at).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
            })
          : '';

        const agentName = evt.related_agent_id ? evt.related_agent_id.toUpperCase() : evt.source.toUpperCase();

        return (
          <div
            key={evt.id}
            className="flex items-start gap-3 p-2.5 rounded border border-gray-100 bg-white hover:border-gray-200 transition-colors shadow-2xs"
          >
            <div className="mt-1">
              <span className="w-2 h-2 rounded-full bg-blue-500 inline-block" />
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2 mb-0.5">
                <span className="font-semibold text-gray-900 tracking-tight">
                  {agentName}
                </span>
                <span className="text-[10px] text-gray-400">{timeStr}</span>
              </div>

              <div className="text-gray-600 truncate">{evt.event_type}</div>

              {evt.payload && Object.keys(evt.payload).length > 0 && (
                <div className="mt-1 text-[11px] text-gray-500 bg-gray-50 px-2 py-1 rounded truncate border border-gray-100">
                  {evt.payload.title ||
                    evt.payload.summary ||
                    evt.payload.tool ||
                    evt.payload.action ||
                    evt.payload.status ||
                    JSON.stringify(evt.payload)}
                </div>
              )}
            </div>

            {evt.related_agent_id && (
              <Badge status={evt.related_agent_id} size="sm" />
            )}
          </div>
        );
      })}
    </div>
  );
};
