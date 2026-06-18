"""Tests for services/subscription_service.py quota enforcement.

The whole subscription system is gated by SUBSCRIPTION_ENABLED. These tests
toggle that module flag with monkeypatch and use the deterministic 'datastudio'
run-class (which doesn't depend on the model registry) to exercise the
allow / block / metering logic against an in-memory DB.
"""
from services import subscription_service as ss


def _free_user():
    # No `subscription` key → resolves to the free plan.
    return {'_id': 'user-abc', 'email': 'q@example.com'}


def test_check_quota_is_noop_when_subscriptions_disabled(monkeypatch):
    monkeypatch.setattr(ss, 'SUBSCRIPTION_ENABLED', False)
    ok, info = ss.check_quota(_free_user(), 'datastudio')
    assert ok is True and info is None


def test_check_quota_allows_when_under_limit(app, db, monkeypatch):
    monkeypatch.setattr(ss, 'SUBSCRIPTION_ENABLED', True)
    ok, info = ss.check_quota(_free_user(), 'datastudio')
    assert ok is True and info is None


def test_check_quota_blocks_at_limit(app, db, monkeypatch):
    monkeypatch.setattr(ss, 'SUBSCRIPTION_ENABLED', True)
    user = _free_user()
    limit = ss.PLANS['free']['limits']['datastudio']
    db.usage_counters.insert_one({
        'user_id': str(user['_id']),
        'period': ss.current_period(),
        'datastudio': limit,
    })
    ok, info = ss.check_quota(user, 'datastudio')
    assert ok is False
    assert info['error'] == 'quota_exceeded'
    assert info['run_class'] == 'datastudio'
    assert info['limit'] == limit
    assert info['used'] == limit


def test_record_usage_is_noop_when_disabled(app, db, monkeypatch):
    monkeypatch.setattr(ss, 'SUBSCRIPTION_ENABLED', False)
    ss.record_usage('user-xyz', 'datastudio')
    assert ss.get_usage('user-xyz').get('datastudio', 0) == 0


def test_record_usage_increments_when_enabled(app, db, monkeypatch):
    monkeypatch.setattr(ss, 'SUBSCRIPTION_ENABLED', True)
    ss.record_usage('user-xyz', 'datastudio')
    ss.record_usage('user-xyz', 'datastudio')
    assert ss.get_usage('user-xyz').get('datastudio', 0) == 2
