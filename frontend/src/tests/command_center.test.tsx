import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { Badge } from '../components/common/Badge';
import { OrgGraph } from '../components/common/OrgGraph';
import { LiveActivityStream } from '../components/common/LiveActivityStream';
import { Shell } from '../components/layout/Shell';
import { SystemEvent } from '../types';

describe('VICKY OS Frontend - Core UI Components', () => {
  it('renders Badge component with correct status and styling', () => {
    const { container } = render(<Badge status="ONLINE" />);
    expect(screen.getByText('ONLINE')).toBeDefined();
    expect(container.querySelector('.bg-emerald-500')).toBeDefined();
  });

  it('renders Badge with WARNING / REVIEWING status correctly', () => {
    render(<Badge status="AWAITING_APPROVAL" />);
    expect(screen.getByText('AWAITING_APPROVAL')).toBeDefined();
  });

  it('renders OrgGraph with all 4 agents and human authority', () => {
    render(<OrgGraph activeAgent="pa" />);
    expect(screen.getByText('YOU')).toBeDefined();
    expect(screen.getByText('PA')).toBeDefined();
    expect(screen.getByText('ARCHY')).toBeDefined();
    expect(screen.getByText('ELDER')).toBeDefined();
    expect(screen.getByText('TECHY')).toBeDefined();
    expect(screen.getByText('Organizational Hierarchy')).toBeDefined();
  });

  it('renders LiveActivityStream with events', () => {
    const mockEvents: SystemEvent[] = [
      {
        id: '1',
        event_type: 'task.completed',
        source: 'techy_agent',
        related_agent_id: 'techy',
        payload: { title: 'Docker container inspected' },
        created_at: new Date().toISOString(),
      },
    ];

    render(<LiveActivityStream events={mockEvents} />);
    expect(screen.getByText('TECHY')).toBeDefined();
    expect(screen.getByText('task.completed')).toBeDefined();
    expect(screen.getByText('Docker container inspected')).toBeDefined();
  });

  it('renders Shell layout with all navigation sections', () => {
    render(
      <BrowserRouter>
        <Shell />
      </BrowserRouter>
    );

    expect(screen.getByText('VICKY OS')).toBeDefined();
    expect(screen.getByText('Command Center')).toBeDefined();
    expect(screen.getByText('PA Chat')).toBeDefined();
    expect(screen.getByText('Agents')).toBeDefined();
    expect(screen.getByText('Conversations')).toBeDefined();
    expect(screen.getByText('Projects')).toBeDefined();
    expect(screen.getByText('Tasks')).toBeDefined();
    expect(screen.getByText('Approvals')).toBeDefined();
    expect(screen.getByText('Techy Live')).toBeDefined();
    expect(screen.getByText('Server')).toBeDefined();
    expect(screen.getByText('Memory')).toBeDefined();
    expect(screen.getByText('Decisions')).toBeDefined();
  });
});
