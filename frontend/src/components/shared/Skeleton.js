/**
 * Lightweight skeleton-loader primitives (ROADMAP G).
 *
 * Replaces plain "Loading…" text with shimmer placeholders that match the
 * shape of the content they stand in for, so the layout doesn't jump when real
 * data arrives. Respects prefers-reduced-motion via CSS (the shimmer animation
 * is disabled there — see Skeleton.css).
 */
import './Skeleton.css';

export function Skeleton({ width = '100%', height = 16, radius = 8, style = {} }) {
    return (
        <span
            className="skeleton"
            style={{ width, height, borderRadius: radius, display: 'inline-block', ...style }}
            aria-hidden="true"
        />
    );
}

/** A card-shaped skeleton block, used for grids of cards. */
export function SkeletonCard({ lines = 2 }) {
    return (
        <div className="skeleton-card" aria-hidden="true">
            <Skeleton height={20} width="60%" />
            {Array.from({ length: lines }).map((_, i) => (
                <Skeleton key={i} height={12} width={i === lines - 1 ? '40%' : '90%'} style={{ marginTop: 10 }} />
            ))}
        </div>
    );
}

/** A few table-row skeletons. */
export function SkeletonRows({ rows = 5, cols = 4 }) {
    return (
        <div aria-hidden="true">
            {Array.from({ length: rows }).map((_, r) => (
                <div key={r} className="skeleton-row">
                    {Array.from({ length: cols }).map((_, c) => (
                        <Skeleton key={c} height={14} width={`${100 / cols - 4}%`} />
                    ))}
                </div>
            ))}
        </div>
    );
}

export default Skeleton;
