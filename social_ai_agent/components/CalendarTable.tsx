'use client';

import type { ContentRow } from '@/lib/types';

const STATUS_STYLES: Record<string, string> = {
  Pending:  'bg-yellow-900/30 text-yellow-300 border-yellow-700',
  Writing:  'bg-blue-900/30 text-blue-300 border-blue-700',
  Imaging:  'bg-violet-900/30 text-violet-300 border-violet-700',
  Done:     'bg-emerald-900/30 text-emerald-300 border-emerald-700',
  Error:    'bg-red-900/30 text-red-300 border-red-700',
};

const COL_LABELS = ['Date', 'Topic', 'Status', 'LinkedIn', 'Medium', 'IG', 'YouTube', 'Dev.to', 'Images'];

interface Props {
  rows: ContentRow[];
}

function TruncCell({ text, maxLen = 60 }: { text: string; maxLen?: number }) {
  if (!text) return <span className="text-gray-600">—</span>;
  const truncated = text.length > maxLen ? text.slice(0, maxLen) + '…' : text;
  return <span title={text}>{truncated}</span>;
}

function hasContent(text: string) {
  return text && text.length > 0;
}

export default function CalendarTable({ rows }: Props) {
  if (rows.length === 0) {
    return (
      <div className="card p-10 flex flex-col items-center justify-center text-gray-600">
        <span className="text-4xl mb-3">📋</span>
        <p className="text-sm">No rows yet. Run the pipeline to generate your first entry.</p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead>
            <tr className="border-b border-gray-800">
              {COL_LABELS.map((h) => (
                <th
                  key={h}
                  className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-widest whitespace-nowrap"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr
                key={row.date}
                className={`border-b border-gray-800/60 hover:bg-gray-800/30 transition-colors ${
                  i === 0 ? 'bg-gray-800/20' : ''
                }`}
              >
                <td className="px-4 py-3 whitespace-nowrap text-gray-400 font-mono text-xs">
                  {row.date}
                </td>
                <td className="px-4 py-3 max-w-[200px]">
                  <TruncCell text={row.topic} maxLen={50} />
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <span
                    className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${
                      STATUS_STYLES[row.status] ?? 'bg-gray-800 text-gray-400 border-gray-700'
                    }`}
                  >
                    {row.status}
                  </span>
                </td>
                {[
                  row.linkedinPost,
                  row.mediumArticle,
                  row.igScript,
                  row.ytScript,
                  row.devtoArticle,
                ].map((text, ci) => (
                  <td key={ci} className="px-4 py-3 text-xs text-gray-500 max-w-[140px]">
                    {hasContent(text) ? (
                      <span className="text-emerald-400">✓ {text.length.toLocaleString()} chars</span>
                    ) : (
                      <span className="text-gray-700">—</span>
                    )}
                  </td>
                ))}
                <td className="px-4 py-3 text-xs">
                  {[row.linkedinImage, row.mediumImage, row.igImage].filter(Boolean).length > 0 ? (
                    <span className="text-emerald-400">
                      ✓ {[row.linkedinImage, row.mediumImage, row.igImage].filter(Boolean).length}/3
                    </span>
                  ) : (
                    <span className="text-gray-700">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
