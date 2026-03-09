import React from 'react';
import constants from '../../constants';

export default function DownloadResultsZip({ sessionId, label }) {
    const downloadResultsZip = async () => {
        try {
            const token = localStorage.getItem('aiml_token');
            const endpoint = `${constants.API_BASE_URL}/download-results-zip/${sessionId}`;
            
            const response = await fetch(endpoint, {
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });
            
            if (!response.ok) throw new Error('Download failed');
            
            let filename = `results.zip`;
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
            console.error('Error downloading results zip:', error);
        }
    };

    return (
        <button className="btn-download-secondary" onClick={downloadResultsZip}>
            {label || "📊 Download Results (Zip)"}
        </button>
    );
}
