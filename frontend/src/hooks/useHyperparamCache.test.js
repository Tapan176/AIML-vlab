import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import useHyperparamCache from './useHyperparamCache';

describe('useHyperparamCache', () => {
    let store;
    beforeEach(() => {
        vi.useFakeTimers();
        store = new Map();
        vi.stubGlobal('localStorage', {
            getItem: (k) => (store.has(k) ? store.get(k) : null),
            setItem: (k, v) => store.set(k, String(v)),
            removeItem: (k) => store.delete(k),
            clear: () => store.clear(),
        });
    });
    afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals(); });

    it('debounces rapid edits into a single localStorage write', () => {
        const { result } = renderHook(() => useHyperparamCache('cnn', undefined));
        const setHp = result.current[1];

        act(() => setHp({ epochs: 1 }));
        act(() => setHp({ epochs: 2 }));
        act(() => setHp({ epochs: 3 }));
        // Inside the debounce window nothing is written yet.
        expect(store.get('cnn_hyperparams')).toBeUndefined();

        act(() => vi.advanceTimersByTime(300));
        expect(JSON.parse(store.get('cnn_hyperparams'))).toEqual({ epochs: 3 });
    });

    it('flushes a pending write on unmount', () => {
        const { result, unmount } = renderHook(() => useHyperparamCache('ann', undefined));
        act(() => result.current[1]({ lr: 0.5 }));
        expect(store.get('ann_hyperparams')).toBeUndefined();   // still pending
        act(() => unmount());
        expect(JSON.parse(store.get('ann_hyperparams'))).toEqual({ lr: 0.5 });
    });
});
