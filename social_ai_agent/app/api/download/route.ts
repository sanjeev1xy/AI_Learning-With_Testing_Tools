import { NextResponse } from 'next/server';
import { readFile } from 'fs/promises';
import { excelManager } from '@/lib/excelManager';

export async function GET(): Promise<NextResponse> {
  try {
    const filePath = excelManager.getFilePath();
    const data = await readFile(filePath);
    return new NextResponse(data, {
      headers: {
        'Content-Type':
          'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'Content-Disposition': 'attachment; filename="content_calendar.xlsx"',
      },
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
