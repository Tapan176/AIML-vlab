/**
 * First-run onboarding (ROADMAP D4).
 *
 * A lightweight "get started in 3 steps" modal shown once to a new user (no
 * training sessions yet, and not previously dismissed). It demystifies the
 * core loop — pick a model → load a dataset → train — and links straight into
 * the Lab and Data Studio. Dismissal is remembered in localStorage so it never
 * nags a returning user.
 */
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ROUTES } from '../../constants';
import { overlayVariants, modalVariants, listVariants, itemVariants } from '../../utils/motion';
import './OnboardingModal.css';

export const ONBOARDING_DISMISSED_KEY = 'aiml_onboarding_dismissed';

const STEPS = [
    {
        icon: '🧠',
        title: '1. Pick a model',
        body: 'Open the Lab and choose from 20+ models — regression, classification, clustering, neural nets, NLP and more.',
    },
    {
        icon: '📂',
        title: '2. Load a dataset',
        body: 'Use a built-in sample dataset, or upload your own CSV / image ZIP. Clean it first in Data Studio if you like.',
    },
    {
        icon: '▶️',
        title: '3. Train & explore',
        body: 'Tune hyperparameters, watch live training charts, then download the model or compare runs on your Dashboard.',
    },
];

export default function OnboardingModal({ onClose }) {
    const navigate = useNavigate();

    const dismiss = () => {
        try { localStorage.setItem(ONBOARDING_DISMISSED_KEY, '1'); } catch (e) {}
        onClose();
    };

    const go = (route) => {
        dismiss();
        navigate(route);
    };

    return (
        <motion.div className="onb-overlay" onClick={dismiss}
            variants={overlayVariants} initial="hidden" animate="visible">
            <motion.div className="onb-modal" onClick={e => e.stopPropagation()}
                variants={modalVariants} initial="hidden" animate="visible">
                <button className="onb-close" onClick={dismiss} aria-label="Close">✕</button>
                <div className="onb-hero">
                    <div className="onb-hero-icon">🚀</div>
                    <h2>Welcome to the AI/ML Lab</h2>
                    <p>Train and experiment with machine-learning models right in your browser — no setup required.</p>
                </div>

                <motion.div className="onb-steps" variants={listVariants} initial="hidden" animate="visible">
                    {STEPS.map(s => (
                        <motion.div className="onb-step" key={s.title} variants={itemVariants}>
                            <div className="onb-step-icon">{s.icon}</div>
                            <h4>{s.title}</h4>
                            <p>{s.body}</p>
                        </motion.div>
                    ))}
                </motion.div>

                <div className="onb-actions">
                    <button className="onb-btn-secondary" onClick={() => go(ROUTES.HOME)}>Browse Data Studio</button>
                    <button className="onb-btn-primary" onClick={() => go(ROUTES.LAB)}>Open the Lab →</button>
                </div>
                <button className="onb-skip" onClick={dismiss}>Skip for now</button>
            </motion.div>
        </motion.div>
    );
}
