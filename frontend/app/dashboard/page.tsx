'use client';

import { useQuery } from '@tanstack/react-query';
import { getDashboardSummary } from '@/lib/api';
import { KPICard } from '@/components/dashboard/KPICard';
import { RecoveryFunnel } from '@/components/dashboard/RecoveryFunnel';
import { FailureDistribution } from '@/components/dashboard/FailureDistribution';
import { BaselineComparison } from '@/components/dashboard/BaselineComparison';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { formatCurrency, formatPercent } from '@/lib/utils';
import { RotateCcw } from 'lucide-react';
import { useState } from 'react';

export default function DashboardPage() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: () => getDashboardSummary(),
  });

  const [runningDemo, setRunningDemo] = useState(false);

  const handleRunDemo = async () => {
    setRunningDemo(true);
    try {
      const response = await fetch('http://localhost:5000/api/demo/run', {
        method: 'POST',
      });
      if (response.ok) {
        await refetch();
      }
    } finally {
      setRunningDemo(false);
    }
  };

  const summary = data?.data || {};

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">RecoverAI Dashboard</h1>
          <p className="text-slate-600">Autonomous Revenue Recovery Control Plane</p>
        </div>
        <Button onClick={handleRunDemo} disabled={runningDemo}>
          <RotateCcw className="w-4 h-4 mr-2" />
          {runningDemo ? 'Running Demo...' : 'Run Demo'}
        </Button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <KPICard
          title="Revenue at Risk"
          value={formatCurrency(summary.revenue_at_risk)}
          subtitle={`${summary.total_cases} cases`}
          color="orange"
        />
        <KPICard
          title="Recovered Revenue"
          value={formatCurrency(summary.recovered_revenue)}
          subtitle={`${summary.recovered_cases} recovered`}
          color="green"
        />
        <KPICard
          title="Recovery Rate"
          value={`${summary.recovery_rate?.toFixed(1) || 0}%`}
          subtitle="vs 27.2% baseline"
          color="blue"
        />
        <KPICard
          title="Incremental Recovery"
          value={formatCurrency(summary.incremental_recovery)}
          subtitle="vs naive strategy"
          color="green"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <RecoveryFunnel />
        <FailureDistribution />
      </div>

      <BaselineComparison />

      {/* Active Cases */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Active Cases</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.active_cases || 0}</div>
            <p className="text-xs text-slate-500">Cases in progress</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Blocked Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{summary.blocked_actions || 0}</div>
            <p className="text-xs text-slate-500">Policy violations prevented</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Total Cases</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.total_cases || 0}</div>
            <p className="text-xs text-slate-500">Analyzed by RecoverAI</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
