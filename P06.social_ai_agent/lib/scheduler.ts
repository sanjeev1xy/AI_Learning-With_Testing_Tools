import cron from 'node-cron';
import { runPipeline } from './pipeline';

declare global {
  // eslint-disable-next-line no-var
  var __schedulerStarted: boolean | undefined;
}

export function startScheduler(): void {
  if (global.__schedulerStarted) return;
  global.__schedulerStarted = true;

  // Runs every day at 09:00 local time
  cron.schedule('0 9 * * *', async () => {
    console.log('[Scheduler] 09:00 trigger — starting pipeline…');
    await runPipeline();
  });

  console.log('[Scheduler] Registered daily 09:00 pipeline trigger.');
}
