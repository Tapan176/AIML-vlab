"""
Enterprise Data Preprocessing, Profiling & Pipeline Service.
- Data profiling (column stats, missing%, skew, outliers, quality score)
- Extended operations (IQR capping, power transforms, text cleaning, datetime parsing)
- Pipeline persistence (save/load/list named pipelines)
- Pipeline templates (quick-start patterns)
- Dataset diff/comparison
"""
import pandas as pd
import numpy as np
import json
import os
from io import BytesIO
from datetime import datetime
from mongoDb.connection import get_db
from services.google_drive_service import stream_file_from_drive, upload_file_to_drive
from services.dataset_service import save_dataset
from config import BASE_DIR, ensure_dir

PIPELINES_DIR = os.path.join(BASE_DIR, '.pipelines')
ensure_dir(PIPELINES_DIR)

# ── Pipeline Templates ──────────────────────────────────────────────────

PIPELINE_TEMPLATES = {
    'basic_clean': {'name': 'Basic Clean', 'description': 'Drop missing values, scale to z-scores.', 'operations': [{'action': 'dropna', 'columns': []}, {'action': 'standard_scale', 'columns': []}]},
    'ml_ready_classification': {'name': 'ML-Ready (Classification)', 'description': 'Impute median, label encode, standardize — ready for sklearn classifiers.', 'operations': [{'action': 'drop_constant_columns', 'columns': []}, {'action': 'fillna_median', 'columns': []}, {'action': 'label_encode', 'columns': []}, {'action': 'standard_scale', 'columns': []}]},
    'ml_ready_regression': {'name': 'ML-Ready (Regression)', 'description': 'IQR outlier capping, median impute, robust scale.', 'operations': [{'action': 'iqr_outlier_cap', 'columns': []}, {'action': 'fillna_median', 'columns': []}, {'action': 'robust_scale', 'columns': []}]},
    'nlp_clean': {'name': 'NLP Text Clean', 'description': 'Lowercase, strip whitespace, drop missing.', 'operations': [{'action': 'text_lowercase', 'columns': []}, {'action': 'text_strip', 'columns': []}, {'action': 'dropna', 'columns': []}]},
    'full_auto': {'name': 'Full Auto', 'description': 'Aggressive: constant drop, IQR cap, median impute, robust scale, label encode.', 'operations': [{'action': 'drop_constant_columns', 'columns': []}, {'action': 'drop_high_null', 'columns': []}, {'action': 'iqr_outlier_cap', 'columns': []}, {'action': 'fillna_median', 'columns': []}, {'action': 'robust_scale', 'columns': []}, {'action': 'label_encode', 'columns': []}]},
}

def get_pipeline_templates():
    return {k: {'name': v['name'], 'description': v['description'], 'operations': v['operations']} for k, v in PIPELINE_TEMPLATES.items()}

# ── Pipeline Persistence ────────────────────────────────────────────────

def save_pipeline(user_id, pipeline_name, operations):
    db = get_db()
    existing = db.pipelines.find_one({'user_id': str(user_id), 'name': pipeline_name})
    if existing:
        db.pipelines.update_one({'_id': existing['_id']}, {'$set': {'operations': operations, 'updated_at': datetime.utcnow()}})
        return str(existing['_id'])
    result = db.pipelines.insert_one({'user_id': str(user_id), 'name': pipeline_name, 'operations': operations, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()})
    return str(result.inserted_id)

def load_pipeline(user_id, pipeline_name):
    db = get_db()
    doc = db.pipelines.find_one({'user_id': str(user_id), 'name': pipeline_name})
    if not doc: raise ValueError(f"Pipeline '{pipeline_name}' not found.")
    return doc['operations']

def list_pipelines(user_id):
    db = get_db()
    docs = list(db.pipelines.find({'user_id': str(user_id)}).sort('updated_at', -1))
    for d in docs:
        d['_id'] = str(d['_id'])
        d['op_count'] = len(d.get('operations', []))
        for k in ('created_at', 'updated_at'):
            if k in d and hasattr(d[k], 'isoformat'): d[k] = d[k].isoformat()
    return docs

def delete_pipeline(user_id, pipeline_name):
    db = get_db()
    r = db.pipelines.delete_one({'user_id': str(user_id), 'name': pipeline_name})
    if r.deleted_count == 0: raise ValueError(f"Pipeline '{pipeline_name}' not found.")

# ── Data Profiling ──────────────────────────────────────────────────────

def profile_dataset(user_id, dataset_id):
    """Generate column-level stats: dtype, missing%, cardinality, skew, outliers, quality score 0-100."""
    db = get_db()
    from bson import ObjectId
    dataset = db.datasets.find_one({'_id': ObjectId(dataset_id), 'user_id': str(user_id)})
    if not dataset: raise ValueError("Dataset not found or unauthorized")
    if dataset.get('file_type') != 'csv': raise ValueError("Profiling only supports CSV files.")
    df = _load_df(dataset)
    total_rows = len(df)
    profile = {'dataset_id': dataset_id, 'filename': dataset.get('filename'), 'total_rows': total_rows, 'total_columns': len(df.columns), 'total_missing': int(df.isnull().sum().sum()), 'duplicate_rows': int(df.duplicated().sum()), 'quality_score': 0, 'columns': {}, 'suggestions': []}
    penalties = 0
    for col in df.columns:
        cd = df[col]; mc = int(cd.isnull().sum()); mp = round(mc / total_rows * 100, 2) if total_rows > 0 else 0
        card = int(cd.nunique()); cr = round(card / total_rows, 4) if total_rows > 0 else 0
        cp = {'dtype': str(cd.dtype), 'missing_count': mc, 'missing_pct': mp, 'cardinality': card, 'cardinality_ratio': cr, 'is_constant': card <= 1}
        if pd.api.types.is_numeric_dtype(cd):
            clean = cd.dropna()
            if len(clean) > 0:
                cp['min'] = round(float(clean.min()), 4); cp['max'] = round(float(clean.max()), 4); cp['mean'] = round(float(clean.mean()), 4); cp['median'] = round(float(clean.median()), 4); cp['std'] = round(float(clean.std()), 4); cp['skew'] = round(float(clean.skew()), 4) if len(clean) > 1 else 0
                cp['p25'] = round(float(clean.quantile(0.25)), 4); cp['p75'] = round(float(clean.quantile(0.75)), 4)
                iqr = cp['p75'] - cp['p25']; lower = cp['p25'] - 1.5 * iqr; upper = cp['p75'] + 1.5 * iqr
                oc = int(((clean < lower) | (clean > upper)).sum()); cp['outlier_count'] = oc; cp['outlier_pct'] = round(oc / len(clean) * 100, 2) if len(clean) > 0 else 0
                if abs(cp['skew']) > 2: cp['high_skew'] = True; penalties += 1
        vals = cd.dropna().unique()[:5].tolist()
        try: vals = [int(x) if isinstance(x, np.integer) else float(x) if isinstance(x, np.floating) else str(x) for x in vals]
        except: vals = [str(x) for x in vals]
        cp['sample_values'] = vals
        profile['columns'][col] = cp
        if mp > 50: penalties += 3; profile['suggestions'].append(f"Column '{col}': >50% missing — consider dropping.")
        elif mp > 20: penalties += 1; profile['suggestions'].append(f"Column '{col}': {mp:.1f}% missing.")
        if card == 1: penalties += 2; profile['suggestions'].append(f"Column '{col}': constant — safe to drop.")
        if cr > 0.9 and card > 10: penalties += 1; profile['suggestions'].append(f"Column '{col}': very high cardinality ({card} unique).")
    if profile['duplicate_rows'] > 0:
        dp = round(profile['duplicate_rows'] / total_rows * 100, 2) if total_rows > 0 else 0
        profile['suggestions'].append(f"{profile['duplicate_rows']} duplicate rows ({dp}%).")
    mx = max(profile['total_columns'] * 10 + 10, 20)
    score = max(0, min(100, round(100 - (penalties / mx) * 100)))
    profile['quality_score'] = score
    if score < 40: profile['suggestions'].append("⚠️ Low quality score — run Full Auto Pipeline.")
    elif score < 70: profile['suggestions'].append("🔶 Fair quality — address missing values.")
    return profile

def diff_datasets(user_id, dataset_id_a, dataset_id_b):
    """Compare two datasets: shape delta, column diff, numeric drift."""
    db = get_db(); from bson import ObjectId
    da = db.datasets.find_one({'_id': ObjectId(dataset_id_a), 'user_id': str(user_id)})
    db_ = db.datasets.find_one({'_id': ObjectId(dataset_id_b), 'user_id': str(user_id)})
    if not da or not db_: raise ValueError("Both datasets must exist and belong to user.")
    dfa = _load_df(da); dfb = _load_df(db_)
    diff = {'dataset_a': {'filename': da['filename'], 'rows': len(dfa), 'cols': len(dfa.columns)}, 'dataset_b': {'filename': db_['filename'], 'rows': len(dfb), 'cols': len(dfb.columns)}, 'rows_delta': len(dfb) - len(dfa), 'columns_added': list(set(dfb.columns) - set(dfa.columns)), 'columns_removed': list(set(dfa.columns) - set(dfb.columns)), 'columns_common': list(set(dfa.columns) & set(dfb.columns)), 'numeric_drift': {}}
    for col in diff['columns_common']:
        if pd.api.types.is_numeric_dtype(dfa[col]) and pd.api.types.is_numeric_dtype(dfb[col]):
            ma = float(dfa[col].mean()); mb = float(dfb[col].mean()); d = round(mb - ma, 4)
            if abs(d) > 0.001: diff['numeric_drift'][col] = {'mean_before': ma, 'mean_after': mb, 'drift': d}
    return diff

# ── Internal Helpers ────────────────────────────────────────────────────

def _load_df(dataset):
    if not dataset.get('drive_id'): raise ValueError("Dataset missing Google Drive ID.")
    fh, _ = stream_file_from_drive(dataset['drive_id']); return pd.read_csv(fh)

def _auto_columns(df, action):
    """Auto-select relevant columns based on operation type."""
    if action in ('standard_scale', 'minmax_scale', 'robust_scale', 'fillna_mean', 'fillna_median', 'iqr_outlier_cap', 'power_transform'):
        return df.select_dtypes(include=[np.number]).columns.tolist()
    if action in ('label_encode',): return df.select_dtypes(include=['object', 'category']).columns.tolist()
    if action in ('text_lowercase', 'text_strip', 'text_clean'): return df.select_dtypes(include=['object']).columns.tolist()
    return df.columns.tolist()

def _apply_operation(df, action, columns):
    """Apply a single operation. Supports 20+ operation types."""
    if not columns or len(columns) == 0: columns = _auto_columns(df, action)
    if not columns: return df
    try:
        if action == 'dropna': df = df.dropna(subset=[c for c in columns if c in df.columns])
        elif action == 'fillna_mean':
            for col in columns:
                if col in df.columns and pd.api.types.is_numeric_dtype(df[col]): df[col] = df[col].fillna(df[col].mean())
        elif action == 'fillna_median':
            for col in columns:
                if col in df.columns and pd.api.types.is_numeric_dtype(df[col]): df[col] = df[col].fillna(df[col].median())
        elif action == 'fillna_mode':
            for col in columns:
                if col in df.columns:
                    m = df[col].mode(); df[col] = df[col].fillna(m[0]) if len(m) > 0 else df[col]
        elif action == 'drop_columns': df = df.drop(columns=[c for c in columns if c in df.columns], errors='ignore')
        elif action == 'drop_constant_columns':
            cc = [c for c in columns if c in df.columns and df[c].nunique() <= 1]
            if cc: df = df.drop(columns=cc)
        elif action == 'drop_high_null':
            hn = [c for c in columns if c in df.columns and df[c].isnull().mean() > 0.3]
            if hn: df = df.drop(columns=hn)
        elif action == 'standard_scale':
            from sklearn.preprocessing import StandardScaler
            nc = [c for c in columns if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
            if nc: df[nc] = StandardScaler().fit_transform(df[nc].fillna(0))
        elif action == 'minmax_scale':
            from sklearn.preprocessing import MinMaxScaler
            nc = [c for c in columns if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
            if nc: df[nc] = MinMaxScaler().fit_transform(df[nc].fillna(0))
        elif action == 'robust_scale':
            from sklearn.preprocessing import RobustScaler
            nc = [c for c in columns if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
            if nc: df[nc] = RobustScaler().fit_transform(df[nc].fillna(0))
        elif action == 'iqr_outlier_cap':
            for col in columns:
                if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                    q1 = df[col].quantile(0.25); q3 = df[col].quantile(0.75); iqr = q3 - q1
                    df[col] = df[col].clip(q1 - 1.5 * iqr, q3 + 1.5 * iqr)
        elif action == 'label_encode':
            from sklearn.preprocessing import LabelEncoder
            for col in columns:
                if col in df.columns: df[col] = LabelEncoder().fit_transform(df[col].astype(str))
        elif action == 'one_hot_encode':
            vc = [c for c in columns if c in df.columns and df[c].nunique() <= 50]
            if vc: df = pd.get_dummies(df, columns=vc)
        elif action == 'text_lowercase':
            for col in columns:
                if col in df.columns: df[col] = df[col].astype(str).str.lower()
        elif action == 'text_strip':
            for col in columns:
                if col in df.columns: df[col] = df[col].astype(str).str.strip()
        elif action == 'text_clean':
            import re
            for col in columns:
                if col in df.columns: df[col] = df[col].astype(str).apply(lambda x: re.sub(r'[^a-zA-Z0-9\\s.,!?-]', '', x).strip())
        elif action == 'power_transform':
            from sklearn.preprocessing import PowerTransformer
            nc = [c for c in columns if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
            if nc: df[nc] = PowerTransformer(method='yeo-johnson').fit_transform(df[nc].fillna(0))
        elif action == 'log_transform':
            for col in columns:
                if col in df.columns and pd.api.types.is_numeric_dtype(df[col]): df[col] = np.log1p(df[col].clip(lower=0))
        elif action == 'parse_datetime':
            for col in columns:
                if col in df.columns:
                    try:
                        p = pd.to_datetime(df[col], errors='coerce')
                        df[f'{col}_year'] = p.dt.year; df[f'{col}_month'] = p.dt.month; df[f'{col}_day'] = p.dt.day; df[f'{col}_dow'] = p.dt.dayofweek
                        df = df.drop(columns=[col])
                    except: pass
        elif action == 'drop_duplicates':
            s = [c for c in columns if c in df.columns] if columns else None
            df = df.drop_duplicates(subset=s if s else None)
    except Exception as e:
        raise ValueError(f"Failed applying '{action}' on {columns}: {str(e)}")
    return df

def _ensure_unique_filename(user_id, base_filename):
    db = get_db()
    name, ext = base_filename.rsplit('.', 1) if '.' in base_filename else (base_filename, '')
    counter = 1; nf = base_filename
    while db.datasets.find_one({'user_id': str(user_id), 'filename': nf}):
        nf = f"{name}_processed_v{counter}.{ext}" if ext else f"{name}_processed_v{counter}"; counter += 1
    return nf

def ensure_unique_filename(user_id, base_filename):
    """Backward-compatible wrapper."""
    return _ensure_unique_filename(user_id, base_filename)

def perform_preprocessing(current_user, dataset_id, operations):
    """Retrieve dataset, apply operations chain, save as new versioned dataset in Drive.
    
    Uses a STABLE output filename so repeated runs on the same source produce 
    versioned records (v1, v2, ...) — each with its own drive_id, independently
    downloadable. Provenance chain (source_dataset_id, operation_history) is
    persisted so diffs work across preprocessing runs.
    """
    db = get_db(); from bson import ObjectId
    dataset = db.datasets.find_one({'_id': ObjectId(dataset_id), 'user_id': current_user['_id']})
    if not dataset: raise ValueError("Dataset not found or unauthorized")
    if dataset.get('file_type') != 'csv': raise ValueError("Preprocessing only supports CSV files.")
    if not dataset.get('drive_id'): raise ValueError("Dataset missing Google Drive configuration.")
    fh, _ = stream_file_from_drive(dataset['drive_id']); df = pd.read_csv(fh)
    br, bc = len(df), len(df.columns)
    for op in operations: df = _apply_operation(df, op.get('action'), op.get('columns', []))
    ar, ac = len(df), len(df.columns)
    out = BytesIO(); df.to_csv(out, index=False); out.seek(0)

    # Stable output filename → save_dataset auto-increments version
    src_name = dataset['filename']
    src_base = src_name.rsplit('.', 1)[0] if '.' in src_name else src_name
    output_filename = f"{src_base}_preprocessed.csv"

    # `out` is a seekable BytesIO — pass it straight to the uploader, which wraps
    # it in MediaIoBaseUpload (needs both .read() and .seek()).
    dr = upload_file_to_drive(out, output_filename, folder_type='datasets', user_id=current_user['_id'])
    meta = save_dataset(user_id=current_user['_id'], filename=output_filename, filepath="", file_type='csv', drive_id=dr.get('id'))
    meta['_id'] = str(meta['_id'])
    ts = {'rows_before': br, 'rows_after': ar, 'cols_before': bc, 'cols_after': ac, 'operations_applied': len(operations), 'operations': [o.get('action') for o in operations]}
    meta['transform_summary'] = ts
    meta['source_dataset_id'] = dataset_id

    # Persist provenance
    try:
        db.datasets.update_one({'_id': ObjectId(meta['_id'])}, {'$set': {
            'source_dataset_id': dataset_id, 'source_filename': src_name,
            'operation_history': ts['operations'], 'transform_summary': ts
        }})
    except Exception: pass
    return meta
