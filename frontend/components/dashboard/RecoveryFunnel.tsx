'use client';

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { getDashboardFunnel } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export function RecoveryFunnel() {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard', 'funnel'],
    queryFn: () => getDashboardFunnel(),
  });

  if (isLoading) return <div>Loading...</div>;

  const stages = data?.data?.stages || [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recovery Funnel</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={stages}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
