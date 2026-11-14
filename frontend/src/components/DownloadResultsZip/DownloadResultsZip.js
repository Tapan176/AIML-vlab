import DownloadButton from '../shared/DownloadButton';

export default function DownloadResultsZip({ sessionId, label }) {
    return (
        <DownloadButton
            className="btn-download-secondary"
            endpoint={sessionId ? `/download-results-zip/${sessionId}` : null}
            fallbackName="results.zip"
        >
            {label || '📊 Download Results (Zip)'}
        </DownloadButton>
    );
}
