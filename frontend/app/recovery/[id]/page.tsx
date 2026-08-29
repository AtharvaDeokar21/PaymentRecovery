'use client';

import { useQuery } from '@tanstack/react-query';
import { getRecoveryCase, escalateCase } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { formatCurrency, formatDateTime } from '@/lib/utils';
import { RECOVERY_STATUS_COLORS } from '@/lib/constants';
import { useState } from 'react';
import { AlertCircle, CheckCircle, Clock, Zap } from 'lucide-react';

export default function CaseDetailPage({ params }: { params: { id: string } }) {
  const caseId = parseInt(params.id);
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['recovery', 'case', caseId],
    queryFn: () => getRecoveryCase(caseId),
  });

  const [escalating, setEscalating] = useState(false);

  const handleEscalate = async () => {
    setEscalating(true);
    try {
      await escalateCase(caseId);
      await refetch();
    } finally {
      setEscalating(false);
    }
  };

  if (isLoading) return <div className="p-8">Loading...</div>;

  const c = data?.data || {};

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">Recovery Case #{caseId}</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Payment Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Payment Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <p className="text-xs text-slate-500">Amount</p>
              <p className="text-xl font-bold">{formatCurrency(c.revenue_at_risk)}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Failure Code</p>
              <p className="font-mono text-sm">{c.payment?.failure_code}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Attempt</p>
              <p>#{c.payment?.attempt_number}</p>
            </div>
          </CardContent>
        </Card>

        {/* Customer Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Customer</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <p className="text-xs text-slate-500">Name</p>
              <p className="font-semibold">{c.customer?.name}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Success Rate</p>
              <p className="text-lg font-bold">{(c.customer?.success_rate * 100).toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Lifetime Value</p>
              <p>{formatCurrency(c.customer?.lifetime_value)}</p>
            </div>
          </CardContent>
        </Card>

        {/* AI Diagnosis */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">AI Diagnosis</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <p className="text-xs text-slate-500">Category</p>
              <p className="font-semibold">{c.diagnosis}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Recovery Probability</p>
              <p className="text-lg font-bold">{(c.recovery_probability * 100).toFixed(0)}%</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Confidence</p>
              <p>{(c.confidence * 100).toFixed(0)}%</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Status and Actions */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Case Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className={`text-sm px-4 py-2 rounded-full font-medium ${RECOVERY_STATUS_COLORS[c.status]}`}>
                {c.status}
              </span>
              <div>
                <p className="text-sm font-semibold">Recommended Action</p>
                <p className="text-sm text-slate-600">{c.recommended_action}</p>
              </div>
            </div>
            {c.status === 'ACTION_PENDING' && (
              <Button onClick={handleEscalate} variant="secondary" disabled={escalating}>
                {escalating ? 'Escalating...' : 'Escalate to Human Review'}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Timeline */}
      <Card>
        <CardHeader>
          <CardTitle>Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {c.audit_trail?.map((log, idx) => (
              <div key={log.id} className="flex gap-4">
                <div className="flex flex-col items-center">
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
                    <Clock className="w-4 h-4" />
                  </div>
                  {idx < (c.audit_trail?.length || 0) - 1 && <div className="w-0.5 h-12 bg-slate-200 mt-2" />}
                </div>
                <div className="pb-4">
                  <p className="font-semibold text-sm">{log.event_type}</p>
                  <p className="text-xs text-slate-500">{log.actor}</p>
                  {log.action && <p className="text-sm text-slate-700 mt-1">{log.action}</p>}
                  <p className="text-xs text-slate-400 mt-2">{formatDateTime(log.timestamp)}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
