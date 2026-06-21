import { NextResponse } from 'next/server';
import { excelManager } from '@/lib/excelManager';

export async function GET(): Promise<NextResponse> {
  try {
    const today = new Date().toISOString().split('T')[0];
    const row = await excelManager.getRowByDate(today);
    return NextResponse.json(row ?? null);
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
