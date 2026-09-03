'use client';

import { useQuery } from '@tanstack/react-query';
import { getDashboardSummary, listRecoveryCases } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { formatCurrency, formatPercent } from '@/lib/utils';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Loader } from 'lucide-react';

export default function AnalyticsPage() {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['analytics', 'summary'],
    queryFn: () => getDashboardSummary(),
  });

  const { data: casesData, isLoading: casesLoading } = useQuery({
    queryKey: ['analytics', 'cases'],
    queryFn: () => listRecoveryCases(),
  });

  const summaryStats = summary?.data || {};
  const cases = casesData?.data?.cases || [];

  // Prepare status distribution data
  const statusDistribution = cases.reduce((acc: Record<string, number>, c: any) => {
    acc[c.status] = (acc[c.status] || 0) + 1;
    return acc;
  }, {});

  const statusChartData = Object.entries(statusDistribution).map(([status, count]) => ({
    name: status,
    count: count as number,
  }));

  // Prepare amount distribution data
  const amountRanges = [
    { range: '0-5k', min: 0, max: 500000 },
    { range: '5k-10k', min: 500000, max: 1000000 },
    { range: '10k-50k', min: 1000000, max: 5000000 },
    { range: '50k+', min: 5000000, max: Infinity },
  ];

  const amountChartData = amountRanges.map(({ range, min, max }) => ({
    range,
    cases: cases.filter((c: any) => c.revenue_at_risk >= min && c.revenue_at_risk < max).length,
  }));

  if (summaryLoading || casesLoading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <Loader className="w-8 h-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-2">Analytics</h1>
      <p className="text-slate-600 mb-8">Real-time recovery metrics and insights</p>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Total Revenue at Risk</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(summaryStats.revenue_at_risk || 0)}</div>
            <p className="text-xs text-slate-500 mt-2">{summaryStats.total_cases || 0} cases</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Recovered Revenue</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{formatCurrency(summaryStats.recovered_revenue || 0)}</div>
            <p className="text-xs text-slate-500 mt-2">{summaryStats.recovered_cases || 0} recovered</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Recovery Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(summaryStats.recovery_rate || 0).toFixed(1)}%</div>
            <p className="text-xs text-slate-500 mt-2">vs 27.2% baseline</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Incremental Gain</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{formatCurrency(summaryStats.incremental_recovery || 0)}</div>
            <p className="text-xs text-slate-500 mt-2">above baseline</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Status Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Cases by Status</CardTitle>
          </CardHeader>
          <CardContent>
            {statusChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={statusChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-slate-500 text-center py-8">No case data available</p>
            )}
          </CardContent>
        </Card>

        {/* Amount Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Cases by Amount</CardTitle>
          </CardHeader>
          <CardContent>
            {amountChartData.some((d) => d.cases > 0) ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={amountChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="range" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="cases" fill="#10b981" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-slate-500 text-center py-8">No case data available</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Detailed Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-slate-600">Active Cases</p>
              <p className="text-2xl font-bold">{summaryStats.active_cases || 0}</p>
              <p className="text-xs text-slate-500 mt-1">In progress</p>
            </div>
            <div>
              <p className="text-sm text-slate-600">Blocked Actions</p>
              <p className="text-2xl font-bold text-red-600">{summaryStats.blocked_actions || 0}</p>
              <p className="text-xs text-slate-500 mt-1">Policy violations prevented</p>
            </div>
            <div>
              <p className="text-sm text-slate-600">Success Rate vs Baseline</p>
              <p className="text-2xl font-bold text-green-600">
                +{(((summaryStats.recovery_rate || 0) - 27.2) / 27.2 * 100).toFixed(0)}%
              </p>
              <p className="text-xs text-slate-500 mt-1">Improvement</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
