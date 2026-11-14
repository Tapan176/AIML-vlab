import { Component } from 'react';

/**
 * Catches render errors (and failed lazy-chunk loads after a deploy) so one
 * broken page shows a recovery message instead of a blank white screen.
 */
export default class ErrorBoundary extends Component {
    constructor(props) {
        super(props);
        this.state = { error: null };
    }

    static getDerivedStateFromError(error) {
        return { error };
    }

    componentDidCatch(error, info) {
        // eslint-disable-next-line no-console
        console.error('UI error boundary caught:', error, info?.componentStack);
    }

    render() {
        const { error } = this.state;
        if (!error) return this.props.children;

        // A ChunkLoadError usually means a new version was deployed while the
        // tab was open — a reload fetches the new chunk names.
        const isChunkError = /Loading (CSS )?chunk|ChunkLoadError|dynamically imported module/i.test(String(error?.message || error?.name));
        return (
            <div className="not-found" role="alert">
                <h1>{isChunkError ? 'Update available' : 'Something went wrong'}</h1>
                <p>
                    {isChunkError
                        ? 'A newer version of the app was released. Reload to continue.'
                        : 'This page hit an unexpected error. Reloading usually fixes it.'}
                </p>
                <button type="button" className="auth-btn not-found-link" onClick={() => window.location.reload()}>
                    Reload page
                </button>
            </div>
        );
    }
}
