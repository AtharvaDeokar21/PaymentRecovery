'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export function BaselineComparison() {
  const data = [
    {
      name: 'Recovery Rate',
      baseline: 27.2,
      recoverai: 39.4,
    },
    {
      name: 'Revenue Recovered',
      baseline: 264000,
      recoverai: 391000,
    },
    {
      name: 'Actions Taken',
      baseline: 200,
      recoverai: 142,
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>RecoverAI vs Baseline</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="baseline" fill="#9ca3af" name="Naive Retry" />
            <Bar dataKey="recoverai" fill="#3b82f6" name="RecoverAI" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
