'use client';

import type { ContentRow } from '@/lib/types';

const AGENT_FOR_STATUS: Record<string, string> = {
  Pending:  'Agent 1 — Topic Generator',
  Writing:  'Agent 2 — Content Writer',
  Imaging:  'Agent 3 — Image Generator',
  Done:     'Agent 3 — Image Generator',
  Error:    'Pipeline (error state)',
};

interface FileMeta {
  fileModified: string | null;
  fileSize: number;
}

interface Props {
  rows: ContentRow[];
  fileMeta: FileMeta | null;
}

function fmt(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export default function ExcelLog({ rows, fileMeta }: Props) {
  return (
    <div className="space-y-6">
      {/* File info card */}
      <div className="card p-5 flex items-center justify-between flex-wrap gap-4">
        <div className="space-y-1">
          <p className="text-xs text-gray-500 uppercase tracking-widest">Excel File</p>
          <p className="text-sm font-mono text-gray-300">content_calendar.xlsx</p>
          <div className="flex gap-4 text-xs text-gray-500 mt-1">
            <span>
              Size:{' '}
              <span className="text-gray-300">{fileMeta ? fmt(fileMeta.fileSize) : '—'}</span>
            </span>
            <span>
              Modified:{' '}
              <span className="text-gray-300">
                {fileMeta?.fileModified
                  ? new Date(fileMeta.fileModified).toLocaleString()
                  : '—'}
              </span>
            </span>
            <span>
              Rows:{' '}
              <span className="text-gray-300">{rows.length}</span>
            </span>
          </div>
        </div>
        <a
          href="/api/download"
          download="content_calendar.xlsx"
          className="btn-primary"
        >
          ↓ Download .xlsx
        </a>
      </div>

      {/* Per-row log */}
      <div className="card overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-800">
          <h3 className="text-sm font-semibold text-gray-300">Write Log</h3>
          <p className="text-xs text-gray-600 mt-0.5">Last write event per row, inferred from status</p>
        </div>
        {rows.length === 0 ? (
          <p className="p-10 text-center text-gray-600 text-sm">No entries yet.</p>
        ) : (
          <div className="divide-y divide-gray-800">
            {rows.map((row) => {
              const agent = AGENT_FOR_STATUS[row.status] ?? 'Unknown';
              const charCount = [
                row.linkedinPost,
                row.mediumArticle,
                row.igScript,
                row.ytScript,
                row.devtoArticle,
              ]
                .filter(Boolean)
                .reduce((acc, t) => acc + t.length, 0);

              return (
                <div key={row.date} className="px-5 py-4 flex items-start justify-between gap-4 hover:bg-gray-800/20">
                  <div className="space-y-1">
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-mono text-gray-400">{row.date}</span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                          row.status === 'Done'
                            ? 'bg-emerald-900/30 text-emerald-400'
                            : row.status === 'Error'
                            ? 'bg-red-900/30 text-red-400'
                            : 'bg-gray-800 text-gray-400'
                        }`}
                      >
                        {row.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-200">{row.topic}</p>
                    <p className="text-xs text-gray-500">Last write: <span className="text-indigo-400">{agent}</span></p>
                  </div>
                  <div className="text-right text-xs text-gray-500 flex-shrink-0">
                    {charCount > 0 && (
                      <p>{charCount.toLocaleString()} chars written</p>
                    )}
                    {[row.linkedinImage, row.mediumImage, row.igImage].filter(Boolean).length > 0 && (
                      <p className="text-emerald-500 mt-0.5">
                        {[row.linkedinImage, row.mediumImage, row.igImage].filter(Boolean).length} image(s)
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
