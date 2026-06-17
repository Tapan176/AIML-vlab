import constants from '../../constants';

export default function DownloadModelPredictions({ extension, sessionId }) {
    const downloadModelPredictions = async () => {
        if (!sessionId) return;
        try {
            const token = localStorage.getItem('aiml_token');
            const response = await fetch(
                `${constants.API_BASE_URL}/download-model-predictions/${sessionId}`,
                { headers: token ? { Authorization: `Bearer ${token}` } : {} }
            );
            if (!response.ok) throw new Error('Download failed');

            let filename = `predictions${extension || '.csv'}`;
            const disposition = response.headers.get('Content-Disposition');
            if (disposition) {
                const match = disposition.match(/filename[^;=\n]*=(?:(['"])?(.*?)\1|([^;\n]*))/);
                if (match) filename = match[2] || match[3] || filename;
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', filename);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error downloading predictions:', error);
        }
    };

    return (
        <button className="btn-download" onClick={downloadModelPredictions}>
            📊 Download Predictions ({extension})
        </button>
    );
}
