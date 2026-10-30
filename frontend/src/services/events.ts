import { SystemEvent } from '../types';

type EventCallback = (event: SystemEvent) => void;
type StatusCallback = (status: 'connected' | 'connecting' | 'disconnected') => void;

class EventStreamService {
  private eventSource: EventSource | null = null;
  private listeners: Set<EventCallback> = new Set();
  private statusListeners: Set<StatusCallback> = new Set();
  private status: 'connected' | 'connecting' | 'disconnected' = 'disconnected';
  private reconnectTimeout: any = null;

  connect() {
    if (this.eventSource) return;

    this.setStatus('connecting');
    const streamUrl = (import.meta.env.VITE_BACKEND_URL || '') + '/api/events/stream';

    try {
      this.eventSource = new EventSource(streamUrl);

      this.eventSource.onopen = () => {
        this.setStatus('connected');
      };

      this.eventSource.onmessage = (e) => {
        if (!e.data || e.data.trim() === '') return;
        try {
          const parsed = JSON.parse(e.data) as SystemEvent;
          this.notifyListeners(parsed);
        } catch (err) {
          console.warn('Could not parse SSE message:', e.data);
        }
      };

      this.eventSource.onerror = () => {
        this.setStatus('disconnected');
        this.disconnect();
        // Automatic retry with gentle backoff
        clearTimeout(this.reconnectTimeout);
        this.reconnectTimeout = setTimeout(() => {
          this.connect();
        }, 5000);
      };
    } catch (err) {
      this.setStatus('disconnected');
    }
  }

  disconnect() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    clearTimeout(this.reconnectTimeout);
  }

  subscribe(callback: EventCallback): () => void {
    this.listeners.add(callback);
    if (!this.eventSource) {
      this.connect();
    }
    return () => {
      this.listeners.delete(callback);
    };
  }

  subscribeStatus(callback: StatusCallback): () => void {
    this.statusListeners.add(callback);
    callback(this.status);
    return () => {
      this.statusListeners.delete(callback);
    };
  }

  private setStatus(newStatus: 'connected' | 'connecting' | 'disconnected') {
    this.status = newStatus;
    this.statusListeners.forEach((cb) => {
      try {
        cb(newStatus);
      } catch (err) {
        console.error('Error in status callback:', err);
      }
    });
  }

  private notifyListeners(event: SystemEvent) {
    this.listeners.forEach((cb) => {
      try {
        cb(event);
      } catch (err) {
        console.error('Error in event callback:', err);
      }
    });
  }
}

export const eventStream = new EventStreamService();
