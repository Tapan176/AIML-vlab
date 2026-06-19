import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { getSchema, peekSchema, _clearMemCache } from './schemaCache';

const SCHEMA = { learning_rate: { type: 'float', default: 0.01 } };

describe('schemaCache', () => {
    beforeEach(() => {
        _clearMemCache();
        // Stub a complete localStorage (the ambient test shim lacks clear()).
        const store = new Map();
        vi.stubGlobal('localStorage', {
            getItem: (k) => (store.has(k) ? store.get(k) : null),
            setItem: (k, v) => store.set(k, String(v)),
            removeItem: (k) => store.delete(k),
            clear: () => store.clear(),
        });
        globalThis.fetch = vi.fn(() =>
            Promise.resolve({ json: () => Promise.resolve({ schema: SCHEMA }) }),
        );
    });

    afterEach(() => vi.unstubAllGlobals());

    it('fetches once and persists to localStorage', async () => {
        const schema = await getSchema('cnn');
        expect(schema).toEqual(SCHEMA);
        expect(globalThis.fetch).toHaveBeenCalledTimes(1);
        expect(JSON.parse(localStorage.getItem('aiml:schema:cnn')).schema).toEqual(SCHEMA);
    });

    it('serves from localStorage after a reload (mem cleared) without refetching', async () => {
        await getSchema('cnn');     // populates localStorage
        _clearMemCache();           // simulate a page reload (module memory gone)
        globalThis.fetch.mockClear();
        expect(peekSchema('cnn')).toEqual(SCHEMA);
        expect(globalThis.fetch).not.toHaveBeenCalled();
    });

    it('ignores a version-mismatched persisted entry', () => {
        localStorage.setItem('aiml:schema:cnn', JSON.stringify({ v: 999, t: Date.now(), schema: SCHEMA }));
        expect(peekSchema('cnn')).toBeNull();
    });

    it('ignores an expired persisted entry', () => {
        const stale = Date.now() - 48 * 60 * 60 * 1000;
        localStorage.setItem('aiml:schema:cnn', JSON.stringify({ v: 1, t: stale, schema: SCHEMA }));
        expect(peekSchema('cnn')).toBeNull();
    });
});
