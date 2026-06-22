import ExcelJS from 'exceljs';
import path from 'path';
import type { ContentRow, StatusType } from './types';

const XLSX_PATH = path.join(process.cwd(), 'content_calendar.xlsx');
const SHEET_NAME = 'Content Calendar';

const HEADERS = [
  'Date',
  'Topic',
  'LinkedIn POST',
  'Medium Article',
  'IG Script',
  'YT Script',
  'Dev.to Article',
  'Status',
  'LinkedIn Image',
  'Medium Image',
  'IG Image',
];

const COL: Record<keyof ContentRow, number> = {
  date: 1,
  topic: 2,
  linkedinPost: 3,
  mediumArticle: 4,
  igScript: 5,
  ytScript: 6,
  devtoArticle: 7,
  status: 8,
  linkedinImage: 9,
  mediumImage: 10,
  igImage: 11,
};

function cellStr(cell: ExcelJS.Cell): string {
  const v = cell.value;
  if (v === null || v === undefined) return '';
  if (v instanceof Date) return v.toISOString().split('T')[0];
  if (typeof v === 'object' && 'richText' in v) {
    const rt = v as { richText: Array<{ text: string }> };
    return rt.richText.map((r) => r.text).join('');
  }
  if (typeof v === 'object' && 'text' in v) {
    return String((v as { text: string }).text);
  }
  return String(v);
}

class ExcelManager {
  private lockTail: Promise<void> = Promise.resolve();

  private async withLock<T>(fn: () => Promise<T>): Promise<T> {
    let release!: () => void;
    const next = new Promise<void>((res) => {
      release = res;
    });
    const prev = this.lockTail;
    this.lockTail = next;
    await prev;
    try {
      return await fn();
    } finally {
      release();
    }
  }

  private async open(): Promise<{ wb: ExcelJS.Workbook; ws: ExcelJS.Worksheet }> {
    const wb = new ExcelJS.Workbook();
    try {
      await wb.xlsx.readFile(XLSX_PATH);
    } catch {
      // File doesn't exist yet — bootstrap it
      const fresh = wb.addWorksheet(SHEET_NAME);
      const headerRow = fresh.addRow(HEADERS);
      headerRow.font = { bold: true };
      headerRow.fill = {
        type: 'pattern',
        pattern: 'solid',
        fgColor: { argb: 'FF1E293B' },
      };
      fresh.columns = HEADERS.map(() => ({ width: 30 }));
      await wb.xlsx.writeFile(XLSX_PATH);
    }
    const ws = wb.getWorksheet(SHEET_NAME) ?? wb.addWorksheet(SHEET_NAME);
    if (ws.rowCount === 0) {
      ws.addRow(HEADERS).font = { bold: true };
    }
    return { wb, ws };
  }

  async getAllRows(): Promise<ContentRow[]> {
    return this.withLock(async () => {
      const { ws } = await this.open();
      const rows: ContentRow[] = [];
      ws.eachRow((row, idx) => {
        if (idx === 1) return;
        const date = cellStr(row.getCell(COL.date));
        if (!date) return;
        rows.push({
          date,
          topic: cellStr(row.getCell(COL.topic)),
          linkedinPost: cellStr(row.getCell(COL.linkedinPost)),
          mediumArticle: cellStr(row.getCell(COL.mediumArticle)),
          igScript: cellStr(row.getCell(COL.igScript)),
          ytScript: cellStr(row.getCell(COL.ytScript)),
          devtoArticle: cellStr(row.getCell(COL.devtoArticle)),
          status: (cellStr(row.getCell(COL.status)) as StatusType) || 'Pending',
          linkedinImage: cellStr(row.getCell(COL.linkedinImage)),
          mediumImage: cellStr(row.getCell(COL.mediumImage)),
          igImage: cellStr(row.getCell(COL.igImage)),
        });
      });
      return rows;
    });
  }

  async getRowByDate(date: string): Promise<ContentRow | null> {
    const rows = await this.getAllRows();
    return rows.find((r) => r.date === date) ?? null;
  }

  async appendRow(data: {
    date: string;
    topic: string;
    status: StatusType;
  }): Promise<void> {
    return this.withLock(async () => {
      const { wb, ws } = await this.open();
      ws.addRow([
        data.date,
        data.topic,
        '', '', '', '', '',
        data.status,
        '', '', '',
      ]);
      await wb.xlsx.writeFile(XLSX_PATH);
    });
  }

  async updateRow(date: string, updates: Partial<ContentRow>): Promise<void> {
    return this.withLock(async () => {
      const { wb, ws } = await this.open();
      let found = false;
      ws.eachRow((row, idx) => {
        if (idx === 1) return;
        if (cellStr(row.getCell(COL.date)) !== date) return;
        found = true;
        for (const [key, val] of Object.entries(updates) as [keyof ContentRow, string][]) {
          if (val !== undefined) {
            row.getCell(COL[key]).value = val;
          }
        }
      });
      if (!found) throw new Error(`No row found for date ${date}`);
      await wb.xlsx.writeFile(XLSX_PATH);
    });
  }

  getFilePath(): string {
    return XLSX_PATH;
  }

  async getFileStat(): Promise<{ size: number; mtime: Date } | null> {
    const { stat } = await import('fs/promises');
    try {
      const s = await stat(XLSX_PATH);
      return { size: s.size, mtime: s.mtime };
    } catch {
      return null;
    }
  }
}

// Survive Next.js HMR in dev
declare global {
  // eslint-disable-next-line no-var
  var __excelManager: ExcelManager | undefined;
}

export const excelManager: ExcelManager =
  global.__excelManager ?? (global.__excelManager = new ExcelManager());
