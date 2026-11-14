import DownloadButton from '../shared/DownloadButton';

export default function DownloadTrainedModel({ selectedModel, extension, sessionId, label }) {
    const endpoint = sessionId
        ? `/download-trained-model/${sessionId}`
        : `/download-trained-model?model_name=${encodeURIComponent(selectedModel || '')}&extension=${encodeURIComponent(extension || '.pkl')}`;
    return (
        <DownloadButton className="btn-download-primary" endpoint={endpoint} fallbackName={`${selectedModel}${extension || ''}`}>
            {label || `📦 Download Trained Model (${extension})`}
        </DownloadButton>
    );
}
