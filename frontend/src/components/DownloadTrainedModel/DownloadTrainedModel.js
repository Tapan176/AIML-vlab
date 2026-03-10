import constants from '../../constants';

export default function DownloadTrainedModel({ selectedModel, extension, sessionId, label }) {
    const downloadTrainedModel = async () => {
        try {
            const token = localStorage.getItem('aiml_token');
            const endpoint = sessionId 
                ? `${constants.API_BASE_URL}/download-trained-model/${sessionId}`
                : `${constants.API_BASE_URL}/download-trained-model?model_name=${selectedModel}&extension=${extension}`;
            
            const response = await fetch(endpoint, {
                headers: token && sessionId ? { 'Authorization': `Bearer ${token}` } : {}
            });
            
            if (!response.ok) throw new Error('Download failed');
            
            // Try to get filename from Content-Disposition header
            let filename = `${selectedModel}${extension}`;
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
            console.error('Error downloading model:', error);
        }
    };

    return (
        <button className="btn-download-primary" onClick={downloadTrainedModel}>
            {label || `📦 Download Trained Model (${extension})`}
        </button>
    );
}
