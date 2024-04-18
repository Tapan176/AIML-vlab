import React, { useState, useEffect, useRef } from 'react';

// Custom hook for debouncing
function useDebounce(value, delay) {
    const [debouncedValue, setDebouncedValue] = useState(value);

    useEffect(() => {
        const handler = setTimeout(() => {
            setDebouncedValue(value);
        }, delay);

        return () => {
            clearTimeout(handler);
        };
    }, [value, delay]);

    return debouncedValue;
}

const Image = ({ src, alt, style }) => {
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const imgRef = useRef(null);

    const debouncedSrc = useDebounce(src, 300); // Debounce src change with a 300ms delay

    const handleError = () => {
        setError('Failed to load image');
        setIsLoading(false);
    };

    useEffect(() => {
        const img = imgRef.current || new Image();
        imgRef.current = img;

        const handleLoad = () => {
            setIsLoading(false);
        };

        img.addEventListener('load', handleLoad);
        img.addEventListener('error', handleError);

        img.src = debouncedSrc;

        return () => {
            img.removeEventListener('load', handleLoad);
            img.removeEventListener('error', handleError);
        };
    }, [debouncedSrc]);

    // Reset loading state when src changes (debounced)
    useEffect(() => {
        setIsLoading(true); // Set loading state when src changes
    }, [debouncedSrc]);

    return (
        <div style={style}>
            {isLoading && <div>Loading image...</div>}
            {error && <div>Error: {error}</div>}
            <img
                src={debouncedSrc}
                alt={alt}
                style={{
                    display: isLoading || error ? 'none' : 'block',
                    transition: 'opacity 0.3s ease-in-out',
                    opacity: isLoading ? 0 : 1,
                    ...style
                }}
                ref={imgRef}
            />
        </div>
    );
};

export default Image;
