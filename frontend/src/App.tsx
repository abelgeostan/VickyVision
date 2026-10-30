import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Shell } from './components/layout/Shell';
import { CommandCenter } from './pages/CommandCenter';
import { Chat } from './pages/Chat';
import { Agents } from './pages/Agents';
import { Conversations } from './pages/Conversations';
import { Projects } from './pages/Projects';
import { Tasks } from './pages/Tasks';
import { Approvals } from './pages/Approvals';
import { Execution } from './pages/Execution';
import { Server } from './pages/Server';
import { Memory } from './pages/Memory';
import { Decisions } from './pages/Decisions';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Shell />}>
          <Route path="/" element={<CommandCenter />} />
          <Route path="/command-center" element={<CommandCenter />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/conversations" element={<Conversations />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/approvals" element={<Approvals />} />
          <Route path="/execution" element={<Execution />} />
          <Route path="/server" element={<Server />} />
          <Route path="/memory" element={<Memory />} />
          <Route path="/decisions" element={<Decisions />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
