import { describe, it, expect, vi, beforeEach } from 'vitest';
import api, { clearCache } from './api';
import { TOKEN_KEY } from '../constants';

// Minimal fetch Response stand-in (api.js reads res.text()).
function res(body, status = 200) {
  return { ok: status >= 200 && status < 300, status, text: async () => JSON.stringify(body) };
}

// Use a deterministic in-memory localStorage stub. (Node 25 ships an
// experimental global localStorage that shadows jsdom's and lacks a usable
// clear(), so we don't rely on the environment's implementation.)
beforeEach(() => {
  vi.unstubAllGlobals();
  const store = new Map();
  vi.stubGlobal('localStorage', {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: (k) => store.delete(k),
    clear: () => store.clear(),
  });
  clearCache();
});

describe('api.get — dedup + cache', () => {
  it('collapses concurrent identical GETs into a single fetch', async () => {
    const fetchMock = vi.fn().mockResolvedValue(res({ ok: 1 }));
    vi.stubGlobal('fetch', fetchMock);
    const [a, b] = await Promise.all([api.get('/x'), api.get('/x')]);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(a).toEqual({ ok: 1 });
    expect(b).toEqual({ ok: 1 });
  });

  it('serves a cached copy within TTL (no second fetch)', async () => {
    const fetchMock = vi.fn().mockResolvedValue(res({ v: 2 }));
    vi.stubGlobal('fetch', fetchMock);
    await api.get('/y');
    await api.get('/y');
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('returns a clone so a caller mutating the result cannot poison the cache', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(res({ nested: { a: 1 } })));
    const first = await api.get('/z');
    first.nested.a = 999;
    const second = await api.get('/z'); // served from cache
    expect(second.nested.a).toBe(1);
  });
});

describe('api writes — cache invalidation', () => {
  it('a POST clears the GET cache so the next GET refetches', async () => {
    const fetchMock = vi.fn().mockResolvedValue(res({ v: 1 }));
    vi.stubGlobal('fetch', fetchMock);
    await api.get('/list');            // fetch #1 (cached)
    await api.post('/list', { a: 1 }); // fetch #2 (+ clears cache)
    await api.get('/list');            // fetch #3 (cache cleared → refetch)
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });
});

describe('api — 401 handling', () => {
  it('clears the stored token and throws on 401', async () => {
    localStorage.setItem(TOKEN_KEY, 'expired-token');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(res({ error: 'unauthorized' }, 401)));
    await expect(api.get('/secure', { ttl: 0 })).rejects.toThrow(/Session expired/);
    expect(localStorage.getItem(TOKEN_KEY)).toBeNull();
  });
});
