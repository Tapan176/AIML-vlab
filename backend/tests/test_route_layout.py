"""Tests that the dataset- and pipeline-domain endpoints split out of
``utils/route.py`` (Phase 4) still resolve at their unchanged ``/api`` paths and
now live on the new ``datasets_routes`` / ``pipelines_routes`` blueprints.

This is a pure-move refactor: every full URL must stay identical so the frontend
sees no change. The app is built straight from the factory with the real DB and
migrations off — no Mongo needed; we only inspect the URL map.
"""
from app import create_app


def _rule_map():
    """Build the app and return {rule_string: set(endpoint_names)}.

    A path like ``/api/pipelines`` is served by two endpoints (GET + POST), so a
    single rule string can map to several endpoints — hence a set.
    """
    app = create_app(
        testing=True, init_database=False, run_migrations_on_start=False,
    )
    mapping = {}
    for rule in app.url_map.iter_rules():
        mapping.setdefault(rule.rule, set()).add(rule.endpoint)
    return mapping


def test_moved_routes_still_resolve_at_unchanged_paths():
    rules = set(_rule_map().keys())
    expected = {
        '/api/upload',
        '/api/datasets/default',
        '/api/datasets/<dataset_id>',
        '/api/datasets/preprocess',
        '/api/datasets/<dataset_id>/profile',
        '/api/datasets/diff',
        '/api/datasets/<dataset_id>/preview',
        '/api/datasets/versions/<filename>',
        '/api/datasets/<dataset_id>/folder-images',
        '/api/datasets/save-annotations',
        '/api/pipelines',
        '/api/pipelines/templates',
        '/api/pipelines/<pipeline_name>',
    }
    missing = expected - rules
    assert not missing, f"expected routes missing from url_map: {sorted(missing)}"


def test_dataset_routes_moved_to_datasets_blueprint():
    mapping = _rule_map()
    for path in (
        '/api/upload',
        '/api/datasets/preprocess',
        '/api/datasets/save-annotations',
        '/api/datasets/<dataset_id>/preview',
    ):
        endpoints = mapping[path]
        assert endpoints, f"no endpoint registered for {path}"
        assert all(e.startswith('datasets_routes.') for e in endpoints), (
            f"{path} should be served by datasets_routes, got {sorted(endpoints)}"
        )


def test_pipeline_routes_moved_to_pipelines_blueprint():
    mapping = _rule_map()
    for path in ('/api/pipelines', '/api/pipelines/templates', '/api/pipelines/<pipeline_name>'):
        endpoints = mapping[path]
        assert endpoints, f"no endpoint registered for {path}"
        assert all(e.startswith('pipelines_routes.') for e in endpoints), (
            f"{path} should be served by pipelines_routes, got {sorted(endpoints)}"
        )


def test_moved_endpoints_no_longer_on_utils_blueprint():
    """The split endpoints must not linger on utils_routes (no duplicate rules)."""
    mapping = _rule_map()
    moved_paths = {
        '/api/upload',
        '/api/datasets/preprocess',
        '/api/datasets/save-annotations',
        '/api/datasets/<dataset_id>/preview',
        '/api/pipelines',
        '/api/pipelines/templates',
    }
    for path in moved_paths:
        endpoints = mapping[path]
        assert not any(e.startswith('utils_routes.') for e in endpoints), (
            f"{path} still has a utils_routes endpoint: {sorted(endpoints)}"
        )


def test_download_and_misc_endpoints_remain_on_utils_blueprint():
    """The endpoints intentionally LEFT in utils/route.py stay on utils_routes.

    Keyed by path → the specific utils_routes endpoint that must be present.
    NOTE: ``/api/training-sessions/<session_id>/result-images`` is ALSO served by
    ``model_routes.get_session_result_images`` — a pre-existing duplicate rule
    unrelated to this split — so we assert the utils endpoint is *present* rather
    than the sole handler for that path.
    """
    mapping = _rule_map()
    expected = {
        '/api/download-trained-model': 'utils_routes.download_model',
        '/api/download-trained-model/<session_id>': 'utils_routes.download_model_session',
        '/api/download-results-zip/<session_id>': 'utils_routes.download_results_zip_session',
        '/api/download-model-predictions/<session_id>': 'utils_routes.download_model_predictions_session',
        '/api/training-sessions/<session_id>/result-images': 'utils_routes.get_result_images',
        '/api/feedback': 'utils_routes.submit_feedback',
        '/api/models/info': 'utils_routes.get_models_info',
        '/api/config': 'utils_routes.public_config',
        '/api/models/registry': 'utils_routes.get_model_registry_route',
    }
    for path, endpoint in expected.items():
        assert endpoint in mapping.get(path, set()), (
            f"{path} should remain served by {endpoint}, got {sorted(mapping.get(path, set()))}"
        )
