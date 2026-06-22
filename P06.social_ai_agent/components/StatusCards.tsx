'use client';

import type { ContentRow, StatusResponse } from '@/lib/types';

const STATUS_COLORS: Record<string, string> = {
  Pending:  'bg-yellow-900/40 text-yellow-300 border-yellow-700',
  Writing:  'bg-blue-900/40 text-blue-300 border-blue-700',
  Imaging:  'bg-violet-900/40 text-violet-300 border-violet-700',
  Done:     'bg-emerald-900/40 text-emerald-300 border-emerald-700',
  Error:    'bg-red-900/40 text-red-300 border-red-700',
};

function KeyIndicator({ label, ok }: { label: string; ok: boolean }) {
  return (
    <span className="flex items-center gap-1.5 text-xs">
      <span className={`w-2 h-2 rounded-full ${ok ? 'bg-emerald-400' : 'bg-red-400'}`} />
      <span className={ok ? 'text-gray-400' : 'text-red-400'}>{label}</span>
    </span>
  );
}

interface Props {
  todayRow: ContentRow | null;
  status: StatusResponse | null;
  onRun: () => void;
  isRunning: boolean;
}

export default function StatusCards({ todayRow, status, onRun, isRunning }: Props) {
  const statusColor = todayRow?.status
    ? STATUS_COLORS[todayRow.status] ?? 'bg-gray-800 text-gray-400'
    : 'bg-gray-800 text-gray-500';

  const nextRun = status?.nextRunAt
    ? new Date(status.nextRunAt).toLocaleString()
    : '—';

  return (
    <div className="space-y-4">
      {/* Header bar */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">ContentForge</h1>
          <p className="text-xs text-gray-500 mt-0.5">Automated content pipeline · local-first</p>
        </div>
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <KeyIndicator label="Groq" ok={status?.groqOk ?? false} />
            <KeyIndicator label="Gemini" ok={status?.geminiOk ?? false} />
          </div>
          <span className="text-xs text-gray-500">Next run: {nextRun}</span>
          <button
            onClick={onRun}
            disabled={isRunning}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isRunning ? (
              <>
                <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                {status?.step ?? 'Running…'}
              </>
            ) : (
              '▶ Run Pipeline Now'
            )}
          </button>
        </div>
      </div>

      {/* Cards row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card p-4">
          <p className="text-xs text-gray-500 mb-1 uppercase tracking-widest">Today's Topic</p>
          <p className="text-sm font-semibold text-white leading-snug">
            {todayRow?.topic ?? '—'}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-xs text-gray-500 mb-1 uppercase tracking-widest">Pipeline Status</p>
          {todayRow?.status ? (
            <span className={`inline-block text-xs font-semibold px-2.5 py-1 rounded-full border ${statusColor}`}>
              {todayRow.status}
            </span>
          ) : (
            <p className="text-sm text-gray-500">No data today</p>
          )}
          {status?.error && (
            <p className="text-xs text-red-400 mt-2 break-all">{status.error}</p>
          )}
        </div>
        <div className="card p-4">
          <p className="text-xs text-gray-500 mb-1 uppercase tracking-widest">Last Completed</p>
          <p className="text-sm text-white">
            {status?.lastCompletedAt
              ? new Date(status.lastCompletedAt).toLocaleString()
              : '—'}
          </p>
          {status?.startedAt && (
            <p className="text-xs text-gray-500 mt-1">
              Started {new Date(status.startedAt).toLocaleTimeString()}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
