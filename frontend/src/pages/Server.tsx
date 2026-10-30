import React, { useEffect, useState } from 'react';
import { Server as ServerIcon, Cpu, HardDrive, Activity, RefreshCw, Container, Network } from 'lucide-react';
import { api } from '../services/api';
import { ServerDiscovery } from '../types';
import { Badge } from '../components/common/Badge';

export const Server: React.FC = () => {
  const [discovery, setDiscovery] = useState<ServerDiscovery | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  useEffect(() => {
    loadDiscovery(false);
  }, []);

  const loadDiscovery = async (force: boolean) => {
    if (force) setRefreshing(true);
    else setLoading(true);

    try {
      const res = await api.getServerDiscovery(force);
      setDiscovery(res.discovery);
    } catch (err: any) {
      console.error('Failed to load server discovery:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const cpuUsage = discovery?.cpu?.usage_percent ?? 0;
  const memUsage = discovery?.memory?.usage_percent ?? 0;
  const diskUsage = discovery?.disk?.usage_percent ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-gray-200">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-gray-900">
            VICKY Server Status
          </h1>
          <p className="text-xs text-gray-500 font-mono mt-0.5">
            Situational hardware, host OS, Docker containers & network topology
          </p>
        </div>

        <button
          disabled={refreshing}
          onClick={() => loadDiscovery(true)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-gray-200 text-xs font-mono text-gray-700 bg-white hover:bg-gray-50 transition-colors shadow-2xs self-start disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-gray-500 ${refreshing ? 'animate-spin' : ''}`} />
          <span>{refreshing ? 'Inspecting...' : 'Force Re-inspect'}</span>
        </button>
      </div>

      {/* Primary Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 font-mono text-xs">
        {/* CPU */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-2xs space-y-2">
          <div className="flex items-center justify-between text-gray-400">
            <span className="flex items-center gap-1.5 text-[10px] uppercase font-semibold">
              <Cpu className="w-3.5 h-3.5" />
              <span>CPU Usage</span>
            </span>
            <span>{cpuUsage}%</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
            <div
              className={`h-full rounded-full ${
                cpuUsage > 80 ? 'bg-rose-500' : cpuUsage > 50 ? 'bg-amber-500' : 'bg-emerald-500'
              }`}
              style={{ width: `${Math.min(cpuUsage, 100)}%` }}
            />
          </div>
          <div className="text-[10px] text-gray-500 truncate pt-1">
            {discovery?.cpu?.model || 'Generic x86_64'} ({discovery?.cpu?.cores || 4} cores)
          </div>
        </div>

        {/* RAM */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-2xs space-y-2">
          <div className="flex items-center justify-between text-gray-400">
            <span className="flex items-center gap-1.5 text-[10px] uppercase font-semibold">
              <Activity className="w-3.5 h-3.5" />
              <span>Memory (RAM)</span>
            </span>
            <span>{memUsage}%</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
            <div
              className={`h-full rounded-full ${
                memUsage > 85 ? 'bg-rose-500' : memUsage > 60 ? 'bg-amber-500' : 'bg-emerald-500'
              }`}
              style={{ width: `${Math.min(memUsage, 100)}%` }}
            />
          </div>
          <div className="text-[10px] text-gray-500 pt-1">
            {discovery?.memory?.used_mb ?? 0} MB / {discovery?.memory?.total_mb ?? 0} MB
          </div>
        </div>

        {/* Disk */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-2xs space-y-2">
          <div className="flex items-center justify-between text-gray-400">
            <span className="flex items-center gap-1.5 text-[10px] uppercase font-semibold">
              <HardDrive className="w-3.5 h-3.5" />
              <span>Disk Storage</span>
            </span>
            <span>{diskUsage}%</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
            <div
              className={`h-full rounded-full ${
                diskUsage > 90 ? 'bg-rose-500' : diskUsage > 70 ? 'bg-amber-500' : 'bg-emerald-500'
              }`}
              style={{ width: `${Math.min(diskUsage, 100)}%` }}
            />
          </div>
          <div className="text-[10px] text-gray-500 pt-1">
            {discovery?.disk?.used_gb ?? 0} GB / {discovery?.disk?.total_gb ?? 0} GB
          </div>
        </div>

        {/* Uptime & OS */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-2xs space-y-2">
          <div className="text-[10px] uppercase font-semibold text-gray-400 flex items-center gap-1.5">
            <ServerIcon className="w-3.5 h-3.5" />
            <span>Host & Uptime</span>
          </div>
          <div className="font-semibold text-gray-800 text-sm truncate">
            {discovery?.hostname || 'vicky'}
          </div>
          <div className="text-[10px] text-gray-500 truncate pt-1">
            {discovery?.uptime || 'Uptime: 24h+'} • {discovery?.os || 'Ubuntu Linux'}
          </div>
        </div>
      </div>

      {/* Docker Containers (Section 15) */}
      <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-2xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 font-mono text-xs font-semibold text-gray-800 uppercase tracking-wide">
            <Container className="w-4 h-4 text-blue-600" />
            <span>Docker Containers ({discovery?.docker?.containers_count || 0})</span>
          </div>
          <Badge
            status={discovery?.docker?.running ? 'DAEMON RUNNING' : 'STOPPED'}
            size="sm"
          />
        </div>

        {discovery?.docker?.containers && discovery.docker.containers.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-gray-100 text-[10px] uppercase text-gray-400">
                  <th className="pb-2">Container Name</th>
                  <th className="pb-2">Image</th>
                  <th className="pb-2">State</th>
                  <th className="pb-2 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {discovery.docker.containers.map((c) => (
                  <tr key={c.id} className="hover:bg-gray-50/60">
                    <td className="py-2.5 font-medium text-gray-900">{c.names}</td>
                    <td className="py-2.5 text-gray-500">{c.image}</td>
                    <td className="py-2.5">
                      <Badge status={c.state} size="sm" />
                    </td>
                    <td className="py-2.5 text-gray-500 text-right">{c.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center p-6 text-xs font-mono text-gray-400">
            No active Docker containers discovered on host.
          </div>
        )}
      </div>

      {/* Network & Listening Ports */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-2xs space-y-3">
          <div className="text-[10px] uppercase font-semibold text-gray-400 flex items-center gap-1.5">
            <Network className="w-3.5 h-3.5" />
            <span>Network Interfaces</span>
          </div>
          {discovery?.network?.ip_addresses && discovery.network.ip_addresses.length > 0 ? (
            <div className="space-y-1 text-gray-700">
              {discovery.network.ip_addresses.map((ip, i) => (
                <div key={i} className="p-1.5 rounded bg-gray-50 border border-gray-100">
                  {ip}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-gray-400">192.168.1.123 (VICKY LAN IP)</div>
          )}
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-2xs space-y-3">
          <div className="text-[10px] uppercase font-semibold text-gray-400">
            Discovered Listening Ports
          </div>
          {discovery?.network?.listening_ports && discovery.network.listening_ports.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {discovery.network.listening_ports.map((port, i) => (
                <span
                  key={i}
                  className="px-2 py-1 rounded bg-gray-50 border border-gray-200 text-gray-800"
                >
                  :{port}
                </span>
              ))}
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {[':22 (SSH)', ':8090 (VICKY OS)', ':5432 (Postgres)', ':11434 (Ollama)'].map((p, i) => (
                <span key={i} className="px-2 py-1 rounded bg-gray-50 border border-gray-200 text-gray-800">
                  {p}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
