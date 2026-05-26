/* eslint-disable jsx-a11y/img-redundant-alt */
import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowLeft, faArrowRight } from '@fortawesome/free-solid-svg-icons';

/**
 * Shared carousel for model output visualisations.
 * Renders prev/next navigation and a "Download Current Graph" button.
 */
export default function ImageCarousel({ images, modelName }) {
    const [currentImageIndex, setCurrentImageIndex] = useState(0);

    // Why: reset index when a new training run replaces the image set so we
    // don't try to render index N+1 into a fresh, shorter array.
    useEffect(() => {
        setCurrentImageIndex(0);
    }, [images]);

    if (!images || images.length === 0) return null;

    const downloadCurrentImage = () => {
        const imageUrl = images[currentImageIndex];
        if (!imageUrl) return;
        const link = document.createElement('a');
        link.href = imageUrl;
        link.download = `${modelName}_graph_${currentImageIndex + 1}.jpg`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <div className="output-section">
            <h2>Visualizations</h2>
            <div className="image-carousel">
                <button
                    type="button"
                    className="carousel-btn"
                    onClick={() => setCurrentImageIndex(i => i === 0 ? images.length - 1 : i - 1)}
                >
                    <FontAwesomeIcon icon={faArrowLeft} />
                </button>
                <img src={images[currentImageIndex]} alt={`Output ${currentImageIndex + 1}`} />
                <button
                    type="button"
                    className="carousel-btn"
                    onClick={() => setCurrentImageIndex(i => i === images.length - 1 ? 0 : i + 1)}
                >
                    <FontAwesomeIcon icon={faArrowRight} />
                </button>
            </div>
            <div className="download-section" style={{ marginTop: '12px' }}>
                <button type="button" className="btn-download-primary" onClick={downloadCurrentImage}>
                    Download Current Graph
                </button>
            </div>
        </div>
    );
}
