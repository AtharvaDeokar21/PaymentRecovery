'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { ArrowUp, ArrowDown, TrendingUp } from 'lucide-react';

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: number;
  icon?: React.ReactNode;
  color?: 'blue' | 'green' | 'orange' | 'red';
}

export function KPICard({
  title,
  value,
  subtitle,
  trend,
  icon,
  color = 'blue',
}: KPICardProps) {
  const colorMap = {
    blue: 'bg-blue-100 text-blue-900',
    green: 'bg-green-100 text-green-900',
    orange: 'bg-orange-100 text-orange-900',
    red: 'bg-red-100 text-red-900',
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon && <div className="text-2xl">{icon}</div>}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
        {trend !== undefined && (
          <div className={`flex items-center mt-2 text-xs ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {trend >= 0 ? <ArrowUp className="w-3 h-3 mr-1" /> : <ArrowDown className="w-3 h-3 mr-1" />}
            {Math.abs(trend)}% from last period
          </div>
        )}
      </CardContent>
    </Card>
  );
}
