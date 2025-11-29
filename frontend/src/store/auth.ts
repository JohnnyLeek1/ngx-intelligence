import { atom } from 'jotai';
import { atomWithStorage } from 'jotai/utils';
import type { User, TokenResponse } from '@/types';

// Persist auth token in localStorage
export const authTokenAtom = atomWithStorage<string | null>('auth_token', null);
export const refreshTokenAtom = atomWithStorage<string | null>('refresh_token', null);

// Current user data
export const currentUserAtom = atom<User | null>(null);

// Derived atom for authentication status
// Note: We check localStorage directly as a fallback to handle the initial hydration
// when the page first loads. atomWithStorage may not be hydrated yet on first render.
export const isAuthenticatedAtom = atom((get) => {
  const token = get(authTokenAtom);

  // If token is loaded from atom, use it
  if (token !== null && token !== '') {
    return true;
  }

  // Fallback: check localStorage directly during initial hydration
  // This handles the case where the page just loaded and Jotai hasn't hydrated yet
  const storedToken = typeof window !== 'undefined'
    ? localStorage.getItem('auth_token')
    : null;

  return storedToken !== null && storedToken !== 'null' && storedToken !== '';
});

// Action atom to set authentication tokens
export const setAuthTokensAtom = atom(
  null,
  (_get, set, tokens: TokenResponse) => {
    set(authTokenAtom, tokens.access_token);
    set(refreshTokenAtom, tokens.refresh_token);
  }
);

// Action atom to clear authentication
export const clearAuthAtom = atom(
  null,
  (_get, set) => {
    set(authTokenAtom, null);
    set(refreshTokenAtom, null);
    set(currentUserAtom, null);
  }
);
