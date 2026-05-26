/**
 * Persists the most recently selected dataset for a model page across remounts
 * via localStorage under the key `${modelCode}_dataset`.
 *
 * Replaces the duplicated useState + useEffect + handleDatasetSelect block
 * present in every component under components/Models/.
 */

import { useState, useEffect } from 'react';

export default function useDatasetCache(modelCode) {
    const [datasetData, setDatasetData] = useState('');

    useEffect(() => {
        const cached = localStorage.getItem(`${modelCode}_dataset`);
        if (cached) {
            // Silently ignore corrupt cache entries — the user can just re-pick a dataset.
            try { setDatasetData(JSON.parse(cached)); } catch (e) {}
        }
    }, [modelCode]);

    const handleDatasetSelect = (data) => {
        setDatasetData(data);
        if (data && data.filename) {
            localStorage.setItem(`${modelCode}_dataset`, JSON.stringify(data));
        } else {
            localStorage.removeItem(`${modelCode}_dataset`);
        }
    };

    return { datasetData, handleDatasetSelect };
}
