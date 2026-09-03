'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { AlertCircle, CheckCircle, Loader } from 'lucide-react';
import { getPolicies, updatePolicies } from '@/lib/api';

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    max_retry_attempts: 2,
    max_auto_retry_amount: 1000000,
    min_recovery_probability: 0.65,
    approval_threshold: 1000000,
    cooldown_minutes: 15,
  });
  const [saved, setSaved] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Fetch current policies
  const { data: policiesData, isLoading } = useQuery({
    queryKey: ['policies'],
    queryFn: () => getPolicies(),
  });

  // Update policies when data loads
  useEffect(() => {
    if (policiesData?.data) {
      setSettings(policiesData.data);
    }
  }, [policiesData]);

  const handleChange = (key: string, value: string | number) => {
    setSettings((prev) => ({
      ...prev,
      [key]: typeof value === 'string' ? (key.includes('amount') ? parseInt(value) : parseFloat(value)) : value,
    }));
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      setSaved(false);
      await updatePolicies(settings);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error('Failed to save settings:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const formatCurrency = (paise: number) => {
    return `₹${(paise / 100).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-2">Settings</h1>
      <p className="text-slate-600 mb-8">Manage recovery policy configuration</p>

      {saved && (
        <div className="mb-6 flex items-center gap-2 rounded-lg bg-green-50 px-4 py-3 text-green-700">
          <CheckCircle className="w-5 h-5" />
          <span>Settings saved successfully</span>
        </div>
      )}

      {isLoading && (
        <div className="mb-6 flex items-center gap-2 rounded-lg bg-blue-50 px-4 py-3 text-blue-700">
          <Loader className="w-5 h-5 animate-spin" />
          <span>Loading policies...</span>
        </div>
      )}

      {/* Recovery Policy Settings */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Recovery Policy</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Max Retry Attempts */}
          <div>
            <label className="block text-sm font-medium text-slate-900 mb-2">
              Maximum Retry Attempts
            </label>
            <div className="flex items-center gap-4">
              <input
                type="number"
                value={settings.max_retry_attempts}
                onChange={(e) => handleChange('max_retry_attempts', e.target.value)}
                className="px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 w-32"
                min="1"
                max="10"
              />
              <p className="text-sm text-slate-600">
                How many times the system will automatically retry a failed payment
              </p>
            </div>
          </div>

          {/* Max Auto Retry Amount */}
          <div>
            <label className="block text-sm font-medium text-slate-900 mb-2">
              Maximum Auto-Retry Amount
            </label>
            <div className="flex items-center gap-4">
              <div className="flex items-center border border-slate-300 rounded-lg overflow-hidden">
                <span className="px-4 py-2 bg-slate-100 text-slate-600 font-medium">₹</span>
                <input
                  type="number"
                  value={settings.max_auto_retry_amount / 100}
                  onChange={(e) => handleChange('max_auto_retry_amount', parseInt(e.target.value) * 100)}
                  className="px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 w-40"
                  min="0"
                />
              </div>
              <p className="text-sm text-slate-600">
                Payments above this amount require manual approval
              </p>
            </div>
            <p className="text-xs text-slate-500 mt-2">Current: {formatCurrency(settings.max_auto_retry_amount)}</p>
          </div>

          {/* Min Recovery Probability */}
          <div>
            <label className="block text-sm font-medium text-slate-900 mb-2">
              Minimum Recovery Probability Threshold
            </label>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={settings.min_recovery_probability}
                  onChange={(e) => handleChange('min_recovery_probability', e.target.value)}
                  className="px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 w-32"
                  min="0"
                  max="1"
                  step="0.05"
                />
                <span className="text-slate-600">({(settings.min_recovery_probability * 100).toFixed(0)}%)</span>
              </div>
              <p className="text-sm text-slate-600">
                Minimum confidence level required to automatically attempt recovery
              </p>
            </div>
          </div>

          {/* Approval Threshold */}
          <div>
            <label className="block text-sm font-medium text-slate-900 mb-2">
              Approval Threshold
            </label>
            <div className="flex items-center gap-4">
              <div className="flex items-center border border-slate-300 rounded-lg overflow-hidden">
                <span className="px-4 py-2 bg-slate-100 text-slate-600 font-medium">₹</span>
                <input
                  type="number"
                  value={settings.approval_threshold / 100}
                  onChange={(e) => handleChange('approval_threshold', parseInt(e.target.value) * 100)}
                  className="px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 w-40"
                  min="0"
                />
              </div>
              <p className="text-sm text-slate-600">
                Payments above this amount require merchant approval before escalation
              </p>
            </div>
            <p className="text-xs text-slate-500 mt-2">Current: {formatCurrency(settings.approval_threshold)}</p>
          </div>

          {/* Cooldown */}
          <div>
            <label className="block text-sm font-medium text-slate-900 mb-2">
              Cooldown Period (minutes)
            </label>
            <div className="flex items-center gap-4">
              <input
                type="number"
                value={settings.cooldown_minutes}
                onChange={(e) => handleChange('cooldown_minutes', e.target.value)}
                className="px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 w-32"
                min="1"
                max="1440"
              />
              <p className="text-sm text-slate-600">
                Wait time between consecutive retry attempts for the same payment
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end gap-4">
        <Button
          variant="secondary"
          onClick={() => window.location.reload()}
          disabled={isSaving}
        >
          Cancel
        </Button>
        <Button
          onClick={handleSave}
          disabled={isSaving || isLoading}
        >
          {isSaving ? 'Saving...' : 'Save Settings'}
        </Button>
      </div>

      {/* Policy Summary */}
      <Card className="mt-8">
        <CardHeader>
          <CardTitle className="text-lg">Current Policy Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-slate-600">Auto-Retry Limit</p>
              <p className="text-lg font-semibold">{settings.max_retry_attempts}x</p>
            </div>
            <div>
              <p className="text-sm text-slate-600">Auto-Retry Up To</p>
              <p className="text-lg font-semibold">{formatCurrency(settings.max_auto_retry_amount)}</p>
            </div>
            <div>
              <p className="text-sm text-slate-600">Confidence Threshold</p>
              <p className="text-lg font-semibold">{(settings.min_recovery_probability * 100).toFixed(0)}%</p>
            </div>
            <div>
              <p className="text-sm text-slate-600">Approval Required Above</p>
              <p className="text-lg font-semibold">{formatCurrency(settings.approval_threshold)}</p>
            </div>
            <div>
              <p className="text-sm text-slate-600">Retry Cooldown</p>
              <p className="text-lg font-semibold">{settings.cooldown_minutes}m</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
