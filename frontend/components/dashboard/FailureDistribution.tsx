'use client';

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { getDashboardFailures } from '@/lib/api';
import { PieChart, Pie, Cell, Legend, Tooltip, ResponsiveContainer } from 'recharts';
import { FAILURE_CATEGORIES } from '@/lib/constants';

const COLORS = ['#3b82f6', '#f97316', '#a855f7', '#ef4444', '#06b6d4', '#6b7280'];

export function FailureDistribution() {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard', 'failures'],
    queryFn: () => getDashboardFailures(),
  });

  if (isLoading) return <div>Loading...</div>;

  const distribution = data?.data?.distribution || [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Failure Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={distribution}
              dataKey="count"
              nameKey="category"
              cx="50%"
              cy="50%"
              outerRadius={100}
              label
            >
              {distribution.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
