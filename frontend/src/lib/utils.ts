import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format processing time in milliseconds to a human-readable string
 * @param ms - Time in milliseconds
 * @returns Formatted string (e.g., "234ms", "5.2s", "2m 15s")
 */
export function formatProcessingTime(ms: number | null | undefined): string {
  if (ms === null || ms === undefined) {
    return 'N/A';
  }

  // Less than 1 second: show in milliseconds
  if (ms < 1000) {
    return `${Math.round(ms)}ms`;
  }

  // Less than 1 minute: show in seconds with 1 decimal
  if (ms < 60000) {
    return `${(ms / 1000).toFixed(1)}s`;
  }

  // 1 minute or more: show in minutes and seconds
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.round((ms % 60000) / 1000);

  if (seconds === 0) {
    return `${minutes}m`;
  }

  return `${minutes}m ${seconds}s`;
}
