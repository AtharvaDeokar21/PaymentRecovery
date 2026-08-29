'use client';

import { useQuery } from '@tanstack/react-query';
import { listRecoveryCases } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { RECOVERY_STATUS_COLORS, ACTION_TYPES } from '@/lib/constants';
import { formatCurrency, formatRelativeTime } from '@/lib/utils';
import Link from 'next/link';

export default function RecoveryPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['recovery', 'cases'],
    queryFn: () => listRecoveryCases(),
  });

  const cases = data?.data?.cases || [];

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-2">Recovery Cases</h1>
      <p className="text-slate-600 mb-6">All payment recovery cases and their status</p>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b">
                <tr>
                  <th className="text-left p-4 font-semibold">Payment</th>
                  <th className="text-left p-4 font-semibold">Customer</th>
                  <th className="text-left p-4 font-semibold">Amount</th>
                  <th className="text-left p-4 font-semibold">Failure</th>
                  <th className="text-left p-4 font-semibold">Recovery</th>
                  <th className="text-left p-4 font-semibold">Action</th>
                  <th className="text-left p-4 font-semibold">Status</th>
                  <th className="text-left p-4 font-semibold">Time</th>
                </tr>
              </thead>
              <tbody>
                {cases.map((c) => (
                  <tr key={c.id} className="border-b hover:bg-slate-50">
                    <td className="p-4">
                      <Link href={`/recovery/${c.id}`} className="text-blue-600 hover:underline">
                        #{c.payment_id}
                      </Link>
                    </td>
                    <td className="p-4">{c.customer?.name || 'N/A'}</td>
                    <td className="p-4 font-mono">{formatCurrency(c.revenue_at_risk)}</td>
                    <td className="p-4 text-xs">{c.payment?.failure_code || 'N/A'}</td>
                    <td className="p-4">
                      {c.recovery_probability ? `${(c.recovery_probability * 100).toFixed(0)}%` : 'N/A'}
                    </td>
                    <td className="p-4">{ACTION_TYPES[c.recommended_action] || c.recommended_action || 'N/A'}</td>
                    <td className="p-4">
                      <span className={`text-xs px-2 py-1 rounded-full ${RECOVERY_STATUS_COLORS[c.status]}`}>
                        {c.status}
                      </span>
                    </td>
                    <td className="p-4 text-xs text-slate-500">{formatRelativeTime(c.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {cases.length === 0 && (
            <div className="p-8 text-center text-slate-500">No recovery cases found</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
