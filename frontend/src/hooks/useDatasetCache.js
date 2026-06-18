/**
 * Persists the most recently selected dataset for a model page across remounts
 * via localStorage under the key `${modelCode}_dataset`.
 *
 * Replaces the duplicated useState + useEffect + handleDatasetSelect block
 * present in every component under components/Models/.
 *
 * Also consumes a one-shot "Train on this output" handoff from Data Studio:
 * when sessionStorage holds a `train_handoff` payload, the targeted model page
 * pre-selects that dataset on mount (and clears the handoff so it fires once).
 * See frontend/src/utils/trainHandoff.js.
 */

import { useState, useEffect } from 'react';
import { consumeTrainHandoff } from '../utils/trainHandoff';

export default function useDatasetCache(modelCode) {
    const [datasetData, setDatasetData] = useState('');

    useEffect(() => {
        // A pending "Train on this output" handoff wins over the cached pick:
        // the user explicitly asked to train this model on a fresh dataset.
        const handoff = consumeTrainHandoff(modelCode);
        if (handoff && handoff.filename) {
            const data = {
                filename: handoff.filename,
                dataset_id: handoff.dataset_id || null,
                drive_id: handoff.drive_id || null,
                file_type: handoff.file_type || null,
            };
            setDatasetData(data);
            try { localStorage.setItem(`${modelCode}_dataset`, JSON.stringify(data)); } catch (e) {}
            return;
        }
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
