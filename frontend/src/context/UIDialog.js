/**
 * Global UI dialog system — replaces the browser's native window.alert /
 * window.confirm with on-brand, themed popups.
 *
 *   const { notify, confirm } = useUI();
 *   notify('Saved!', 'success');                 // toast (replaces alert)
 *   const ok = await confirm({                    // Promise<boolean> (replaces window.confirm)
 *       title: 'Delete dataset?',
 *       message: 'This cannot be undone.',
 *       confirmText: 'Delete', danger: true,
 *   });
 *   if (!ok) return;
 *
 * Toasts auto-dismiss (animation-driven) and can be clicked to close early.
 * The confirm dialog resolves true on confirm, false on cancel / overlay click.
 */
import { createContext, useCallback, useContext, useState } from 'react';
import './UIDialog.css';

const UIDialogContext = createContext(null);

export const useUI = () => {
    const ctx = useContext(UIDialogContext);
    if (!ctx) {
        throw new Error('useUI must be used within a UIDialogProvider');
    }
    return ctx;
};

const ICONS = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ',
};

let _toastId = 0;

export function UIDialogProvider({ children }) {
    const [toasts, setToasts] = useState([]);
    const [dialog, setDialog] = useState(null);

    const dismiss = useCallback((id) => {
        setToasts((list) => list.filter((t) => t.id !== id));
    }, []);

    // Show a toast. type: 'info' | 'success' | 'error' | 'warning'.
    const notify = useCallback((message, type = 'info') => {
        if (!message) return;
        const id = ++_toastId;
        setToasts((list) => [...list, { id, message: String(message), type }]);
        return id;
    }, []);

    // Promise-based confirmation. Resolves true (confirm) / false (cancel).
    const confirm = useCallback((opts = {}) => {
        return new Promise((resolve) => {
            setDialog({
                title: opts.title || 'Are you sure?',
                message: opts.message || '',
                confirmText: opts.confirmText || 'Confirm',
                cancelText: opts.cancelText || 'Cancel',
                danger: !!opts.danger,
                resolve,
            });
        });
    }, []);

    const closeDialog = useCallback((result) => {
        setDialog((d) => {
            if (d) d.resolve(result);
            return null;
        });
    }, []);

    return (
        <UIDialogContext.Provider value={{ notify, confirm }}>
            {children}

            {/* Toast stack */}
            <div className="ui-toast-stack" aria-live="polite" aria-atomic="false">
                {toasts.map((t) => (
                    <div
                        key={t.id}
                        className={`ui-toast ui-toast-${t.type}`}
                        role="status"
                        onClick={() => dismiss(t.id)}
                        onAnimationEnd={() => dismiss(t.id)}
                    >
                        <span className="ui-toast-icon">{ICONS[t.type] || ICONS.info}</span>
                        <span className="ui-toast-msg">{t.message}</span>
                    </div>
                ))}
            </div>

            {/* Confirmation dialog */}
            {dialog && (
                <div className="ui-modal-overlay" onClick={() => closeDialog(false)}>
                    <div
                        className="ui-modal"
                        role="dialog"
                        aria-modal="true"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <h2 className={`ui-modal-title${dialog.danger ? ' danger' : ''}`}>
                            {dialog.title}
                        </h2>
                        {dialog.message && (
                            <p className="ui-modal-message">{dialog.message}</p>
                        )}
                        <div className="ui-modal-actions">
                            <button
                                type="button"
                                className="ui-btn ui-btn-secondary"
                                onClick={() => closeDialog(false)}
                            >
                                {dialog.cancelText}
                            </button>
                            <button
                                type="button"
                                className={`ui-btn ${dialog.danger ? 'ui-btn-danger' : 'ui-btn-primary'}`}
                                onClick={() => closeDialog(true)}
                                autoFocus
                            >
                                {dialog.confirmText}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </UIDialogContext.Provider>
    );
}

export default UIDialogProvider;
