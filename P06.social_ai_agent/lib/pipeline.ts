import { excelManager } from './excelManager';
import {
  agent1TopicGenerator,
  agent2ContentWriter,
  agent3ImageGenerator,
  todayISO,
} from './agents';
import type { PipelineState } from './types';

function nextNineAM(): string {
  const now = new Date();
  const next = new Date(now);
  next.setHours(9, 0, 0, 0);
  if (next <= now) next.setDate(next.getDate() + 1);
  return next.toISOString();
}

// Survive HMR in Next.js dev mode
declare global {
  // eslint-disable-next-line no-var
  var __pipelineState: PipelineState | undefined;
}

const state: PipelineState = global.__pipelineState ?? {
  running: false,
  step: '',
  startedAt: null,
  lastCompletedAt: null,
  error: null,
};
global.__pipelineState = state;

export function getPipelineState(): PipelineState & {
  nextRunAt: string;
  groqOk: boolean;
  geminiOk: boolean;
} {
  return {
    ...state,
    nextRunAt: nextNineAM(),
    groqOk: !!process.env.GROQ_API_KEY,
    geminiOk: !!process.env.GEMINI_API_KEY,
  };
}

export async function runPipeline(): Promise<void> {
  if (state.running) {
    console.log('[Pipeline] Already running — skipping duplicate trigger.');
    return;
  }

  state.running = true;
  state.error = null;
  state.startedAt = new Date().toISOString();
  state.step = 'Starting…';

  try {
    const today = todayISO();

    // ── Agent 1 ───────────────────────────────────────────────────────────
    state.step = 'Agent 1 — Topic Generator';
    console.log('[Pipeline] Step 1: Topic Generator');
    const topic = await agent1TopicGenerator();
    console.log(`[Pipeline] Topic: ${topic}`);

    // ── Agent 2 ───────────────────────────────────────────────────────────
    const rowAfterA1 = await excelManager.getRowByDate(today);
    const needsContent = !rowAfterA1?.linkedinPost;

    if (needsContent) {
      state.step = 'Agent 2 — Content Writer';
      console.log('[Pipeline] Step 2: Content Writer');
      await agent2ContentWriter(topic);
    } else {
      console.log('[Pipeline] Step 2: Content already exists — skipping Agent 2.');
    }

    // ── Agent 3 ───────────────────────────────────────────────────────────
    const rowAfterA2 = await excelManager.getRowByDate(today);
    const needsImages = !rowAfterA2?.linkedinImage && !rowAfterA2?.mediumImage;

    if (needsImages) {
      state.step = 'Agent 3 — Image Generator';
      console.log('[Pipeline] Step 3: Image Generator');
      await agent3ImageGenerator(topic);
    } else {
      console.log('[Pipeline] Step 3: Images already exist — skipping Agent 3.');
    }

    state.step = 'Done';
    state.lastCompletedAt = new Date().toISOString();
    console.log('[Pipeline] Complete.');
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    state.error = msg;
    state.step = 'Error';
    console.error('[Pipeline] Failed:', msg);

    // Mark today's row as Error if it exists
    try {
      const today = todayISO();
      const row = await excelManager.getRowByDate(today);
      if (row) await excelManager.updateRow(today, { status: 'Error' });
    } catch {
      // best-effort
    }
  } finally {
    state.running = false;
  }
}
