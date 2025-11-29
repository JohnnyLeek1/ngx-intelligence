import { atom } from 'jotai';
import type { QueueStatsResponse, QueueItem } from '@/types';

// Queue statistics
export const queueStatsAtom = atom<QueueStatsResponse>({
  queued: 0,
  processing: 0,
  completed: 0,
  failed: 0,
  total: 0,
  estimated_time_remaining: undefined,
});

// Current queue items
export const queueItemsAtom = atom<QueueItem[]>([]);

// Queue paused status
export const isQueuePausedAtom = atom<boolean>(false);

// Processing mode
export const processingModeAtom = atom<string>('realtime');
