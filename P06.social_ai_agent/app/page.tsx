'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import StatusCards from '@/components/StatusCards';
import ContentTabs from '@/components/ContentTabs';
import CalendarTable from '@/components/CalendarTable';
import ExcelLog from '@/components/ExcelLog';
import type { ContentRow, StatusResponse } from '@/lib/types';

type MainTab = 'today' | 'calendar' | 'log';

interface StatusWithMeta extends StatusResponse {
  fileModified: string | null;
  fileSize: number;
}

export default function DashboardPage() {
  const [mainTab, setMainTab] = useState<MainTab>('today');
  const [todayRow, setTodayRow] = useState<ContentRow | null>(null);
  const [calendarRows, setCalendarRows] = useState<ContentRow[]>([]);
  const [pipelineStatus, setPipelineStatus] = useState<StatusWithMeta | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isRunning = pipelineStatus?.running ?? false;
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch('/api/status');
      if (res.ok) {
        const data = (await res.json()) as StatusWithMeta;
        setPipelineStatus(data);
      }
    } catch {
      // silently ignore poll failures
    }
  }, []);

  const fetchToday = useCallback(async () => {
    try {
      const res = await fetch('/api/today');
      if (res.ok) {
        const data = (await res.json()) as ContentRow | null;
        setTodayRow(data);
      }
    } catch {
      // silently ignore
    }
  }, []);

  const fetchCalendar = useCallback(async () => {
    try {
      const res = await fetch('/api/calendar');
      if (res.ok) {
        const data = (await res.json()) as ContentRow[];
        setCalendarRows(data);
      }
    } catch {
      // silently ignore
    }
  }, []);

  // Initial load
  useEffect(() => {
    void fetchStatus();
    void fetchToday();
    void fetchCalendar();
  }, [fetchStatus, fetchToday, fetchCalendar]);

  // Adaptive polling: 3s when running, 15s when idle
  useEffect(() => {
    const interval = isRunning ? 3000 : 15000;

    const tick = async () => {
      await fetchStatus();
      await fetchToday();
      if (!isRunning) await fetchCalendar();
    };

    pollRef.current = setTimeout(function loop() {
      void tick().then(() => {
        pollRef.current = setTimeout(loop, isRunning ? 3000 : 15000);
      });
    }, interval);

    return () => {
      if (pollRef.current) clearTimeout(pollRef.current);
    };
  }, [isRunning, fetchStatus, fetchToday, fetchCalendar]);

  // Fetch calendar when switching to its tab
  useEffect(() => {
    if (mainTab === 'calendar' || mainTab === 'log') {
      void fetchCalendar();
    }
  }, [mainTab, fetchCalendar]);

  const handleRunPipeline = async () => {
    setError(null);
    try {
      const res = await fetch('/api/run', { method: 'POST' });
      if (!res.ok) {
        const body = (await res.json()) as { error?: string };
        setError(body.error ?? 'Failed to start pipeline.');
      } else {
        // Immediately poll to pick up the "running" state
        setTimeout(() => void fetchStatus(), 400);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Network error');
    }
  };

  const TABS: { id: MainTab; label: string }[] = [
    { id: 'today',    label: "Today's Content" },
    { id: 'calendar', label: 'Calendar' },
    { id: 'log',      label: 'Excel Log' },
  ];

  return (
    <main className="min-h-screen p-6 max-w-screen-2xl mx-auto space-y-6">
      {/* Status + header */}
      <StatusCards
        todayRow={todayRow}
        status={pipelineStatus}
        onRun={() => void handleRunPipeline()}
        isRunning={isRunning}
      />

      {/* Error banner */}
      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-xl px-4 py-3 text-sm text-red-300 flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-200 text-lg leading-none">×</button>
        </div>
      )}

      {/* Live step indicator when running */}
      {isRunning && pipelineStatus?.step && (
        <div className="bg-indigo-900/20 border border-indigo-800 rounded-xl px-4 py-3 flex items-center gap-3">
          <span className="w-3 h-3 border-2 border-indigo-400/40 border-t-indigo-400 rounded-full animate-spin flex-shrink-0" />
          <span className="text-sm text-indigo-300">{pipelineStatus.step}</span>
        </div>
      )}

      {/* Main tab bar */}
      <div className="flex gap-2">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setMainTab(t.id)}
            className={mainTab === t.id ? 'tab-active' : 'tab-inactive'}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {mainTab === 'today' && <ContentTabs todayRow={todayRow} />}
      {mainTab === 'calendar' && <CalendarTable rows={calendarRows} />}
      {mainTab === 'log' && (
        <ExcelLog
          rows={calendarRows}
          fileMeta={
            pipelineStatus
              ? {
                  fileModified: pipelineStatus.fileModified ?? null,
                  fileSize: pipelineStatus.fileSize ?? 0,
                }
              : null
          }
        />
      )}
    </main>
  );
}
