'use client';

import { useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import type { ContentRow } from '@/lib/types';

// Dynamic import avoids ESM transpile issues with react-markdown in Next.js 14
const ReactMarkdown = dynamic(() => import('react-markdown'), { ssr: false });

const CONTENT_TABS = [
  { id: 'linkedin',  label: 'LinkedIn',  field: 'linkedinPost',  markdown: false },
  { id: 'medium',    label: 'Medium',    field: 'mediumArticle', markdown: true  },
  { id: 'instagram', label: 'Instagram', field: 'igScript',      markdown: false },
  { id: 'youtube',   label: 'YouTube',   field: 'ytScript',      markdown: false },
  { id: 'devto',     label: 'Dev.to',    field: 'devtoArticle',  markdown: true  },
  { id: 'images',    label: 'Images',    field: null,            markdown: false },
] as const;

type TabId = (typeof CONTENT_TABS)[number]['id'];

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const copy = useCallback(() => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [text]);
  return (
    <button onClick={copy} className="btn-ghost text-xs px-3 py-1.5">
      {copied ? '✓ Copied' : 'Copy'}
    </button>
  );
}

function EmptyState({ tab }: { tab: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-gray-600">
      <span className="text-4xl mb-3">🤖</span>
      <p className="text-sm">No {tab} content yet.</p>
      <p className="text-xs mt-1">Run the pipeline to generate it.</p>
    </div>
  );
}

interface Props {
  todayRow: ContentRow | null;
}

export default function ContentTabs({ todayRow }: Props) {
  const [active, setActive] = useState<TabId>('linkedin');

  const current = CONTENT_TABS.find((t) => t.id === active)!;

  const content =
    current.field && todayRow
      ? (todayRow[current.field as keyof ContentRow] as string)
      : '';

  return (
    <div className="card overflow-hidden">
      {/* Tab bar */}
      <div className="flex gap-1 p-2 border-b border-gray-800 overflow-x-auto">
        {CONTENT_TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setActive(t.id)}
            className={active === t.id ? 'tab-active' : 'tab-inactive'}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Content area */}
      <div className="p-4">
        {active === 'images' ? (
          <ImagesPanel row={todayRow} />
        ) : !content ? (
          <EmptyState tab={current.label} />
        ) : (
          <div>
            <div className="flex justify-end mb-3">
              <CopyButton text={content} />
            </div>
            {current.markdown ? (
              <div className="prose-dark max-w-none overflow-y-auto max-h-[60vh]">
                <ReactMarkdown>{content}</ReactMarkdown>
              </div>
            ) : (
              <pre className="whitespace-pre-wrap text-sm text-gray-300 leading-relaxed overflow-y-auto max-h-[60vh]">
                {content}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function ImagesPanel({ row }: { row: ContentRow | null }) {
  if (!row || (!row.mediumImage && !row.linkedinImage && !row.igImage)) {
    return <EmptyState tab="images" />;
  }

  const images = [
    { label: 'Medium Cover (16:9)',      src: row.mediumImage,   aspect: 'aspect-video' },
    { label: 'LinkedIn Banner (16:9)',   src: row.linkedinImage, aspect: 'aspect-video' },
    { label: 'Instagram Square (1:1)',   src: row.igImage,       aspect: 'aspect-square' },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      {images.map(({ label, src, aspect }) =>
        src ? (
          <div key={label} className="space-y-2">
            <p className="text-xs text-gray-400 font-medium">{label}</p>
            <div className={`${aspect} overflow-hidden rounded-lg bg-gray-800`}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={src} alt={label} className="w-full h-full object-cover" />
            </div>
            <a
              href={src}
              download
              className="block text-center text-xs text-indigo-400 hover:text-indigo-300 py-1"
            >
              Download
            </a>
          </div>
        ) : null,
      )}
    </div>
  );
}
