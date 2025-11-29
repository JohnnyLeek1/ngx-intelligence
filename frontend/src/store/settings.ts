import { atom } from 'jotai';
import type { ConfigResponse } from '@/types';

// Full configuration
export const configAtom = atom<ConfigResponse | null>(null);

// Individual configuration sections
export const aiConfigAtom = atom<Record<string, any>>({});
export const processingConfigAtom = atom<Record<string, any>>({});
export const namingConfigAtom = atom<Record<string, any>>({});

// UI preferences
export const sidebarCollapsedAtom = atom<boolean>(false);
export const themeAtom = atom<'light' | 'dark'>('light');
