import { atom } from 'jotai';
import { atomWithStorage } from 'jotai/utils';
import type { User, TokenResponse } from '@/types';

// Persist auth token in localStorage
export const authTokenAtom = atomWithStorage<string | null>('auth_token', null);
export const refreshTokenAtom = atomWithStorage<string | null>('refresh_token', null);

// Current user data
export const currentUserAtom = atom<User | null>(null);

// Derived atom for authentication status
export const isAuthenticatedAtom = atom((get) => {
  const token = get(authTokenAtom);
  return token !== null && token !== '';
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
