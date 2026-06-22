import { NextResponse } from 'next/server';
import { getPipelineState, runPipeline } from '@/lib/pipeline';

export async function POST(): Promise<NextResponse> {
  const state = getPipelineState();
  if (state.running) {
    return NextResponse.json({ error: 'Pipeline is already running.' }, { status: 409 });
  }

  // Fire and forget — client polls /api/status for progress
  runPipeline().catch((err: unknown) => {
    console.error('[/api/run] Unhandled pipeline error:', err);
  });

  return NextResponse.json({ message: 'Pipeline started.' });
}
