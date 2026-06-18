"""Unit tests for services/hyperparam_validator.py.

Pure functions — no app, no DB. These guard the validation rules that protect
every training route, and the schema shape the frontend renders from.
"""
import pytest

from services.hyperparam_validator import validate_hyperparams, get_model_schema


def test_defaults_returned_when_no_user_params():
    out = validate_hyperparams('simple_linear_regression', {})
    assert out['test_size'] == 0.2
    assert out['random_state'] == 42


def test_user_params_override_defaults_but_keep_the_rest():
    out = validate_hyperparams('logistic_regression', {'C': 0.5, 'max_iter': 200})
    assert out['C'] == 0.5
    assert out['max_iter'] == 200
    assert out['solver'] == 'lbfgs'  # untouched default preserved


def test_string_values_are_coerced_to_declared_type():
    out = validate_hyperparams('knn', {'n_neighbors': '7', 'p': '2'})
    assert out['n_neighbors'] == 7 and isinstance(out['n_neighbors'], int)
    assert out['p'] == 2 and isinstance(out['p'], int)


def test_bool_coercion_from_string():
    assert validate_hyperparams('yolo', {'augment': 'false'})['augment'] is False
    assert validate_hyperparams('yolo', {'augment': 'true'})['augment'] is True


def test_value_below_min_raises():
    with pytest.raises(Exception) as exc:
        validate_hyperparams('simple_linear_regression', {'test_size': 0.001})
    assert 'test_size' in str(exc.value)


def test_value_above_max_raises():
    with pytest.raises(Exception):
        validate_hyperparams('knn', {'n_neighbors': 9999})


def test_enum_rejects_invalid_option():
    with pytest.raises(Exception):
        validate_hyperparams('svm', {'kernel': 'banana'})


def test_enum_accepts_valid_option():
    assert validate_hyperparams('svm', {'kernel': 'linear'})['kernel'] == 'linear'


def test_nullable_param_accepts_none():
    assert validate_hyperparams('decision_tree', {'max_depth': None})['max_depth'] is None


def test_non_nullable_none_raises():
    with pytest.raises(Exception):
        validate_hyperparams('knn', {'n_neighbors': None})


def test_unknown_params_are_ignored():
    out = validate_hyperparams('simple_linear_regression', {'not_a_param': 123})
    assert 'not_a_param' not in out


def test_unknown_model_raises():
    with pytest.raises(Exception):
        validate_hyperparams('does_not_exist', {})


def test_get_model_schema_shape():
    schema = get_model_schema('knn')
    assert schema['n_neighbors']['type'] == 'int'
    assert schema['n_neighbors']['default'] == 5
    assert schema['n_neighbors']['min'] == 1
    assert schema['n_neighbors']['max'] == 50


def test_get_model_schema_unknown_model_returns_none():
    assert get_model_schema('does_not_exist') is None
