import { Brain, Monitor } from 'lucide-react';
import type { StateSnapshot } from '../../services/api';
import BrainServerCard from './BrainServerCard';
import WeComClientCard from './WeComClientCard';

interface DashboardProps {
  snapshot: StateSnapshot;
}

export default function Dashboard({ snapshot }: DashboardProps) {
  const hasBrainServers = snapshot.brain_servers && snapshot.brain_servers.length > 0;
  const hasWeComClients = snapshot.wecom_clients && snapshot.wecom_clients.length > 0;

  return (
    <div className="w-full h-full overflow-y-auto p-6 bg-geist-bg-subtle">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* AI 大脑区域 */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <div className="p-2 rounded-lg bg-orange-100">
              <Brain className="w-5 h-5 text-orange-600" />
            </div>
            <h2 className="text-lg font-semibold text-gray-800">AI 大脑</h2>
            {hasBrainServers && (
              <span className="text-xs text-gray-500">
                ({snapshot.brain_servers.length})
              </span>
            )}
          </div>

          {hasBrainServers ? (
            <div className="grid gap-4 md:grid-cols-2">
              {snapshot.brain_servers.map((server) => (
                <BrainServerCard key={server.instance_id} state={server} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 bg-white rounded-xl border border-dashed border-geist-border">
              <div className="text-gray-400 mb-2">暂无 AI 大脑服务器</div>
              <div className="text-xs text-gray-400">等待心跳连接...</div>
            </div>
          )}
        </section>

        {/* 企微区域 */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <div className="p-2 rounded-lg bg-blue-100">
              <Monitor className="w-5 h-5 text-blue-600" />
            </div>
            <h2 className="text-lg font-semibold text-gray-800">企微客户端</h2>
            {hasWeComClients && (
              <span className="text-xs text-gray-500">
                ({snapshot.wecom_clients.length})
              </span>
            )}
          </div>

          {hasWeComClients ? (
            <div className="space-y-4">
              {snapshot.wecom_clients.map((client) => (
                <WeComClientCard key={client.instance_id} state={client} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 bg-white rounded-xl border border-dashed border-geist-border">
              <div className="text-gray-400 mb-2">暂无企微客户端</div>
              <div className="text-xs text-gray-400">等待心跳连接...</div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
