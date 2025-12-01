import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import { format as dateFnsFormat, formatDistanceToNow as dateFnsFormatDistanceToNow, differenceInHours, isToday, isYesterday } from "date-fns"

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

/**
 * Get the user's local timezone
 * @returns IANA timezone string (e.g., "America/Los_Angeles")
 */
export function getUserTimezone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
}

/**
 * Get timezone abbreviation (e.g., "PST", "PDT", "UTC")
 * @returns Timezone abbreviation
 */
export function getTimezoneAbbreviation(): string {
  const date = new Date();
  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZoneName: 'short',
  });

  const parts = formatter.formatToParts(date);
  const timeZonePart = parts.find((part) => part.type === 'timeZoneName');

  return timeZonePart?.value || 'UTC';
}

/**
 * Convert a UTC date string or Date object to the user's local timezone
 * @param date - ISO 8601 string or Date object (assumed to be UTC)
 * @returns Date object in user's local timezone
 */
function parseUTCDate(date: string | Date): Date {
  if (typeof date === 'string') {
    // Parse the ISO string as UTC and return as-is
    // The Date constructor will handle the UTC timestamp correctly
    return new Date(date);
  }
  return date;
}

/**
 * Format a date and time in the user's local timezone
 * @param date - ISO 8601 string or Date object (assumed to be UTC from backend)
 * @param formatString - Format string (default: 'MMM dd, yyyy HH:mm')
 * @returns Formatted date string in local timezone
 */
export function formatDateTime(date: string | Date, formatString: string = 'MMM dd, yyyy HH:mm'): string {
  try {
    const parsedDate = parseUTCDate(date);
    return dateFnsFormat(parsedDate, formatString);
  } catch (error) {
    console.error('Error formatting date:', error);
    return 'Invalid date';
  }
}

/**
 * Format a date (without time) in the user's local timezone
 * @param date - ISO 8601 string or Date object (assumed to be UTC from backend)
 * @returns Formatted date string (e.g., "Dec 15, 2024")
 */
export function formatDate(date: string | Date): string {
  return formatDateTime(date, 'MMM dd, yyyy');
}

/**
 * Format time only in the user's local timezone
 * @param date - ISO 8601 string or Date object (assumed to be UTC from backend)
 * @returns Formatted time string (e.g., "3:45 PM")
 */
export function formatTime(date: string | Date): string {
  return formatDateTime(date, 'h:mm a');
}

/**
 * Format date with timezone indicator
 * @param date - ISO 8601 string or Date object (assumed to be UTC from backend)
 * @param formatString - Format string (default: 'MMM dd, yyyy HH:mm')
 * @returns Formatted date string with timezone (e.g., "Dec 15, 2024 3:45 PM PST")
 */
export function formatDateTimeWithZone(date: string | Date, formatString: string = 'MMM dd, yyyy h:mm a'): string {
  const formatted = formatDateTime(date, formatString);
  const tz = getTimezoneAbbreviation();
  return `${formatted} ${tz}`;
}

/**
 * Format relative time with smart formatting
 * - Recent times: "2 minutes ago", "3 hours ago"
 * - Today: "Today at 3:45 PM"
 * - Yesterday: "Yesterday at 3:45 PM"
 * - Older: "Dec 15, 2024"
 * @param date - ISO 8601 string or Date object (assumed to be UTC from backend)
 * @returns Formatted relative time string in local timezone
 */
export function formatRelativeTime(date: string | Date): string {
  try {
    const parsedDate = parseUTCDate(date);
    const now = new Date();
    const hoursDiff = Math.abs(differenceInHours(now, parsedDate));

    // Less than 24 hours: show relative time
    if (hoursDiff < 24) {
      return dateFnsFormatDistanceToNow(parsedDate, { addSuffix: true });
    }

    // Today: show "Today at HH:mm"
    if (isToday(parsedDate)) {
      return `Today at ${formatTime(parsedDate)}`;
    }

    // Yesterday: show "Yesterday at HH:mm"
    if (isYesterday(parsedDate)) {
      return `Yesterday at ${formatTime(parsedDate)}`;
    }

    // Older: show full date
    return formatDate(parsedDate);
  } catch (error) {
    console.error('Error formatting relative time:', error);
    return 'Invalid date';
  }
}
