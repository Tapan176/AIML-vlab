/**
 * Shared framer-motion variants (ROADMAP G).
 *
 * Centralises the few transitions used across modals/cards so the motion
 * language is consistent. framer-motion already honours the OS
 * prefers-reduced-motion setting when you wrap the app in
 * <MotionConfig reducedMotion="user">, which App does — so these variants stay
 * simple and don't need to branch on the media query themselves.
 */

// Backdrop fade for modal overlays.
export const overlayVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { duration: 0.18 } },
    exit: { opacity: 0, transition: { duration: 0.12 } },
};

// Modal card: subtle scale + lift.
export const modalVariants = {
    hidden: { opacity: 0, scale: 0.96, y: 12 },
    visible: { opacity: 1, scale: 1, y: 0, transition: { type: 'spring', stiffness: 320, damping: 26 } },
    exit: { opacity: 0, scale: 0.97, y: 8, transition: { duration: 0.12 } },
};

// Staggered list/grid entrance (cards).
export const listVariants = {
    visible: { transition: { staggerChildren: 0.05 } },
};
export const itemVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.25 } },
};
