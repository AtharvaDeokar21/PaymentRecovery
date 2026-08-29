'use client';

import { useQuery } from '@tanstack/react-query';
import { listAuditLogs } from '@/lib/api';
import { Card, CardContent } from '@/components/ui/Card';
import { formatDateTime } from '@/lib/utils';

export default function AuditPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['audit', 'logs'],
    queryFn: () => listAuditLogs(),
  });

  const logs = data?.data?.logs || [];

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-2">Audit Trail</h1>
      <p className="text-slate-600 mb-6">Complete audit log of all RecoverAI actions</p>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b">
                <tr>
                  <th className="text-left p-4 font-semibold">Time</th>
                  <th className="text-left p-4 font-semibold">Actor</th>
                  <th className="text-left p-4 font-semibold">Entity</th>
                  <th className="text-left p-4 font-semibold">Event</th>
                  <th className="text-left p-4 font-semibold">Action</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} className="border-b hover:bg-slate-50">
                    <td className="p-4 text-xs">{formatDateTime(log.timestamp)}</td>
                    <td className="p-4 text-xs font-mono">{log.actor}</td>
                    <td className="p-4 text-xs">{log.entity_type} #{log.entity_id}</td>
                    <td className="p-4">
                      <span className="text-xs px-2 py-1 bg-slate-100 rounded">
                        {log.event_type}
                      </span>
                    </td>
                    <td className="p-4 text-xs text-slate-600">{log.action}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {logs.length === 0 && (
            <div className="p-8 text-center text-slate-500">No audit logs</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
