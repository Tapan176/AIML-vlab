import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import useThrottledValue from './useThrottledValue';

describe('useThrottledValue', () => {
    beforeEach(() => vi.useFakeTimers());
    afterEach(() => vi.useRealTimers());

    it('exposes the initial value immediately', () => {
        const { result } = renderHook(({ v }) => useThrottledValue(v, 400), {
            initialProps: { v: 'a' },
        });
        expect(result.current).toBe('a');
    });

    it('holds rapid updates and commits only the latest on the trailing edge', () => {
        const { result, rerender } = renderHook(({ v }) => useThrottledValue(v, 400), {
            initialProps: { v: 0 },
        });
        // Leading commit was 0. Burst of updates inside the window stay collapsed.
        act(() => rerender({ v: 1 }));
        act(() => rerender({ v: 2 }));
        act(() => rerender({ v: 3 }));
        expect(result.current).toBe(0);

        // After the window, exactly one trailing commit carries the latest value.
        act(() => vi.advanceTimersByTime(400));
        expect(result.current).toBe(3);
    });

    it('always settles on the final value', () => {
        const { result, rerender } = renderHook(({ v }) => useThrottledValue(v, 400), {
            initialProps: { v: 10 },
        });
        act(() => rerender({ v: 20 }));
        act(() => vi.advanceTimersByTime(1000));
        expect(result.current).toBe(20);
    });
});
