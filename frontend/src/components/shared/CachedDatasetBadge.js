import { truncateName } from '../../utils/truncateName';

/**
 * Standardised "✓ Cached dataset: <name>" confirmation shown on every model
 * page once a dataset has been selected/cached. Centralising it keeps the
 * label, truncation length and hover-tooltip behaviour consistent app-wide
 * (replaces the inline block that was duplicated across ~17 model pages).
 *
 * @param {object} props
 * @param {string} props.filename  The cached dataset filename (may be long).
 * @param {string} [props.label]   Override the default "Cached dataset" label
 *                                  (e.g. "Cached image directory" for CNN/ResNet).
 * @param {number} [props.maxLength=44] Characters before middle-truncation.
 */
export default function CachedDatasetBadge({ filename, label = 'Cached dataset', maxLength = 44 }) {
    if (!filename) return null;
    return (
        <div className="cached-dataset-badge" style={{ marginTop: '10px', color: '#34c759' }}>
            ✓ {label}: <strong title={filename}>{truncateName(filename, maxLength)}</strong>
        </div>
    );
}
