import DownloadButton from '../shared/DownloadButton';

export default function DownloadModelPredictions({ extension, sessionId }) {
    return (
        <DownloadButton
            className="btn-download"
            endpoint={sessionId ? `/download-model-predictions/${sessionId}` : null}
            fallbackName={`predictions${extension || '.csv'}`}
        >
            📊 Download Predictions ({extension})
        </DownloadButton>
    );
}
