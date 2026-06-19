import { describe, it, expect } from 'vitest';
import { API_URL } from './config';

// Smoke test under Vitest. Replaces the dead CRA boilerplate App.test.js, which
// asserted a "learn react" link that never existed in this app. Confirms config
// resolves under Vite's import.meta.env.
describe('config', () => {
  it('exposes a non-empty API_URL string', () => {
    expect(typeof API_URL).toBe('string');
    expect(API_URL.length).toBeGreaterThan(0);
  });
});
