import { NextResponse } from 'next/server';
import { getPipelineState } from '@/lib/pipeline';
import { excelManager } from '@/lib/excelManager';

export async function GET(): Promise<NextResponse> {
  try {
    const state = getPipelineState();
    const fileStat = await excelManager.getFileStat();
    return NextResponse.json({
      ...state,
      fileModified: fileStat?.mtime?.toISOString() ?? null,
      fileSize: fileStat?.size ?? 0,
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
