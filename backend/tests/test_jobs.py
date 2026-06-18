"""Tests for the background-job layer (jobs/queue.py + jobs/tasks.py).

No real Redis and no RQ worker: the queue's graceful-degradation paths are
tested directly, enqueue is exercised against fakeredis, and run_training_job is
unit-tested with a stub trainer against the in-memory mongo session record.
"""
import fakeredis

from jobs import queue as jq
from jobs import tasks
from services.training_session_service import create_session, get_session


# ---- queue graceful degradation -------------------------------------------

def test_get_redis_returns_none_without_url(monkeypatch):
    monkeypatch.setattr(jq, 'REDIS_URL', None)
    monkeypatch.setattr(jq, '_redis', None)
    assert jq.get_redis() is None
    assert jq.get_queue() is None


def test_enqueue_returns_none_when_no_queue(monkeypatch):
    monkeypatch.setattr(jq, 'get_queue', lambda: None)
    assert jq.enqueue_training({'model_code': 'x', 'session_id': 's'}) is None


# ---- enqueue against fake redis -------------------------------------------

def test_enqueue_training_places_job_on_queue(monkeypatch):
    fake = fakeredis.FakeStrictRedis()
    monkeypatch.setattr(jq, 'get_redis', lambda: fake)

    payload = {'model_code': 'simple_linear_regression', 'session_id': 'sess1'}
    job = jq.enqueue_training(payload)

    assert job is not None
    assert job.func_name.endswith('run_training_job')
    assert job.args[0] == payload
    assert jq.get_queue().count == 1


# ---- JobRequest shim -------------------------------------------------------

def test_job_request_exposes_json():
    body = {'dataset_id': 'abc', 'hyperparams': {'test_size': 0.2}}
    req = tasks.JobRequest(body)
    assert req.json == body
    assert req.get_json() == body
    assert tasks.JobRequest(None).json == {}


# ---- run_training_job persistence -----------------------------------------

def _stub_resolver(results=None, raises=None):
    def stub(request, validated_params=None, user_id=None, session_version=None):
        if raises:
            raise raises
        return results
    return lambda model_code: stub


def test_run_training_job_records_completed_session(app, db, monkeypatch):
    session = create_session('user-1', 'simple_linear_regression', {'test_size': 0.2})
    monkeypatch.setattr(tasks, 'resolve_train_fn', _stub_resolver(results={
        'evaluation_metrics': {'R2': 0.9},
        'outputImageUrls': [],
        'trained_model_path': '',
        'predictions_output_file': '',
    }))

    out = tasks.run_training_job({
        'model_code': 'simple_linear_regression',
        'session_id': session['_id'],
        'user_id': 'user-1',
        'session_version': session['version'],
        'params': {'test_size': 0.2},
        'request_json': {'dataset_id': 'd1'},
    })

    assert out['status'] == 'completed'
    saved = get_session(session['_id'])
    assert saved['status'] == 'completed'
    assert saved['results']['R2'] == 0.9


def test_run_training_job_records_error_from_result(app, db, monkeypatch):
    session = create_session('user-1', 'simple_linear_regression', {})
    monkeypatch.setattr(tasks, 'resolve_train_fn',
                        _stub_resolver(results={'error': 'bad data'}))

    out = tasks.run_training_job({
        'model_code': 'simple_linear_regression',
        'session_id': session['_id'],
        'params': {},
        'request_json': {},
    })

    assert out['status'] == 'error'
    saved = get_session(session['_id'])
    assert saved['status'] == 'failed'
    assert saved['error'] == 'bad data'


def test_run_training_job_records_error_on_exception(app, db, monkeypatch):
    session = create_session('user-1', 'simple_linear_regression', {})
    monkeypatch.setattr(tasks, 'resolve_train_fn',
                        _stub_resolver(raises=RuntimeError('kaboom')))

    out = tasks.run_training_job({
        'model_code': 'simple_linear_regression',
        'session_id': session['_id'],
        'params': {},
        'request_json': {},
    })

    assert out['status'] == 'error'
    saved = get_session(session['_id'])
    assert saved['status'] == 'failed'
    assert 'kaboom' in saved['error']
