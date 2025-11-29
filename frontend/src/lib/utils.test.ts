import { describe, it, expect } from 'vitest';
import { formatProcessingTime } from './utils';

describe('formatProcessingTime', () => {
  describe('null and undefined handling', () => {
    it('returns "N/A" for null', () => {
      expect(formatProcessingTime(null)).toBe('N/A');
    });

    it('returns "N/A" for undefined', () => {
      expect(formatProcessingTime(undefined)).toBe('N/A');
    });
  });

  describe('milliseconds (< 1 second)', () => {
    it('formats 0ms correctly', () => {
      expect(formatProcessingTime(0)).toBe('0ms');
    });

    it('formats small values in milliseconds', () => {
      expect(formatProcessingTime(234)).toBe('234ms');
    });

    it('formats values just under 1 second', () => {
      expect(formatProcessingTime(999)).toBe('999ms');
    });

    it('rounds decimal milliseconds', () => {
      expect(formatProcessingTime(123.7)).toBe('124ms');
    });
  });

  describe('seconds (1-60 seconds)', () => {
    it('formats exactly 1 second', () => {
      expect(formatProcessingTime(1000)).toBe('1.0s');
    });

    it('formats seconds with 1 decimal place', () => {
      expect(formatProcessingTime(5234)).toBe('5.2s');
    });

    it('formats 10+ seconds correctly', () => {
      expect(formatProcessingTime(10389)).toBe('10.4s');
    });

    it('formats values just under 1 minute', () => {
      expect(formatProcessingTime(59999)).toBe('60.0s');
    });

    it('rounds to 1 decimal place', () => {
      expect(formatProcessingTime(1234)).toBe('1.2s');
      expect(formatProcessingTime(1250)).toBe('1.3s');
    });
  });

  describe('minutes (>= 60 seconds)', () => {
    it('formats exactly 1 minute', () => {
      expect(formatProcessingTime(60000)).toBe('1m');
    });

    it('formats 1 minute with seconds', () => {
      expect(formatProcessingTime(75000)).toBe('1m 15s');
    });

    it('formats multiple minutes', () => {
      expect(formatProcessingTime(125000)).toBe('2m 5s');
    });

    it('formats large values correctly', () => {
      expect(formatProcessingTime(305000)).toBe('5m 5s');
    });

    it('omits seconds when they round to 0', () => {
      expect(formatProcessingTime(120000)).toBe('2m');
      expect(formatProcessingTime(180000)).toBe('3m');
    });

    it('rounds seconds properly', () => {
      expect(formatProcessingTime(125499)).toBe('2m 5s');
      expect(formatProcessingTime(125500)).toBe('2m 6s');
    });

    it('formats values over 10 minutes', () => {
      expect(formatProcessingTime(665000)).toBe('11m 5s');
    });

    it('handles very large values', () => {
      expect(formatProcessingTime(3600000)).toBe('60m');
    });
  });

  describe('edge cases', () => {
    it('handles the boundary at 1000ms', () => {
      expect(formatProcessingTime(999)).toBe('999ms');
      expect(formatProcessingTime(1000)).toBe('1.0s');
    });

    it('handles the boundary at 60000ms', () => {
      expect(formatProcessingTime(59999)).toBe('60.0s');
      expect(formatProcessingTime(60000)).toBe('1m');
    });

    it('handles decimal inputs correctly', () => {
      expect(formatProcessingTime(1234.56)).toBe('1.2s');
    });
  });

  describe('real-world examples', () => {
    it('formats typical fast processing times', () => {
      expect(formatProcessingTime(234)).toBe('234ms');
      expect(formatProcessingTime(567)).toBe('567ms');
    });

    it('formats typical moderate processing times', () => {
      expect(formatProcessingTime(2500)).toBe('2.5s');
      expect(formatProcessingTime(8300)).toBe('8.3s');
    });

    it('formats typical slow processing times', () => {
      expect(formatProcessingTime(95000)).toBe('1m 35s');
      expect(formatProcessingTime(185000)).toBe('3m 5s');
    });
  });
});
