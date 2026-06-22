import { NextResponse } from 'next/server';
import { excelManager } from '@/lib/excelManager';

export async function GET(): Promise<NextResponse> {
  try {
    const rows = await excelManager.getAllRows();
    // Newest date first
    const sorted = [...rows].sort((a, b) => b.date.localeCompare(a.date));
    return NextResponse.json(sorted);
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
