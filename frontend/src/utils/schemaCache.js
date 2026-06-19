/**
 * Model-schema cache with three tiers:
 *   1. in-memory Map  — dedupes concurrent fetches; fastest within a session.
 *   2. localStorage   — survives reloads so a refresh doesn't re-hit the network.
 *   3. network        — GET /model-schema/<code>, the source of truth.
 *
 * The persisted copy is versioned + TTL-bounded: a schema is derived from the
 * backend Pydantic models, so a backend change must eventually win. Bumping
 * VERSION hard-invalidates every persisted schema; the TTL bounds staleness to a
 * day in case VERSION isn't bumped. Schemas are tiny + change rarely, so this is
 * a safe trade for skipping a fetch on every reload.
 */
import constants from '../constants';

const _mem = new Map();                       // modelCode -> schema | Promise<schema>
const VERSION = 1;                            // bump to invalidate all persisted schemas
const TTL_MS = 24 * 60 * 60 * 1000;           // 24h staleness ceiling
const key = (code) => `aiml:schema:${code}`;

function readPersisted(code) {
    try {
        const raw = localStorage.getItem(key(code));
        if (!raw) return null;
        const parsed = JSON.parse(raw);
        if (!parsed || parsed.v !== VERSION || !parsed.t) return null;
        if (Date.now() - parsed.t > TTL_MS) return null;
        return parsed.schema ?? null;
    } catch (e) {
        return null;
    }
}

function writePersisted(code, schema) {
    try {
        localStorage.setItem(key(code), JSON.stringify({ v: VERSION, t: Date.now(), schema }));
    } catch (e) {
        // Storage full / disabled — the in-memory Map still serves this session.
    }
}

/**
 * Synchronous best-effort lookup for the no-flash render path: returns a resolved
 * schema from memory or localStorage, or null when only a fetch can answer.
 */
export function peekSchema(modelCode) {
    const m = _mem.get(modelCode);
    if (m && typeof m.then !== 'function') return m;   // resolved in memory
    if (m) return null;                                // a pending fetch — not ready yet
    const persisted = readPersisted(modelCode);
    if (persisted) {
        _mem.set(modelCode, persisted);
        return persisted;
    }
    return null;
}

/**
 * Resolve a model's schema, hitting the network only when neither cache has it.
 * Returns the schema object directly when cached, else a Promise<schema>.
 */
export function getSchema(modelCode) {
    if (_mem.has(modelCode)) return _mem.get(modelCode);

    const persisted = readPersisted(modelCode);
    if (persisted) {
        _mem.set(modelCode, persisted);
        return persisted;
    }

    const promise = fetch(`${constants.API_BASE_URL}/model-schema/${modelCode}`)
        .then(res => res.json())
        .then(data => {
            const schema = data.schema || null;
            _mem.set(modelCode, schema);
            if (schema) writePersisted(modelCode, schema);
            return schema;
        })
        .catch(err => {
            _mem.delete(modelCode);   // allow retry on next mount
            throw err;
        });
    _mem.set(modelCode, promise);
    return promise;
}

/** Test seam: drop the in-memory tier (localStorage left intact). */
export function _clearMemCache() {
    _mem.clear();
}
