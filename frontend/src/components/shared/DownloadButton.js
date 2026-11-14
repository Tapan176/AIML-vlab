import { useState } from 'react';
import { downloadFile } from '../../services/api';
import { useUI } from '../../context/UIDialog';

/**
 * One authenticated download button used by the trained-model, results-zip
 * and predictions buttons. Shows a busy state and surfaces failures instead
 * of failing silently to the console.
 */
export default function DownloadButton({ endpoint, fallbackName, className, children, disabled }) {
    const [busy, setBusy] = useState(false);
    const { notify } = useUI();

    const onClick = async () => {
        if (!endpoint || busy) return;
        setBusy(true);
        try {
            await downloadFile(endpoint, fallbackName);
        } catch (err) {
            notify(err.message || 'Download failed', 'error');
        } finally {
            setBusy(false);
        }
    };

    return (
        <button type="button" className={className} onClick={onClick} disabled={disabled || busy || !endpoint} aria-busy={busy}>
            {busy ? 'Preparing download…' : children}
        </button>
    );
}
