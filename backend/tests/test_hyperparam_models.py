"""Unit tests for the Pydantic hyperparameter source of truth.

``services/hyperparam_models.py`` holds one Pydantic v2 model per model_code and
derives the legacy ``DEFAULT_HYPERPARAMS`` / ``VALIDATION_SCHEMAS`` /
``PARAM_LABELS`` / ``PARAM_NOTES`` from those models. These tests guard the
collapse: every code in ``config.MODEL_CODES`` must have a model, its defaults
must match what ``validate_hyperparams`` returns for an empty payload, and
``get_model_schema`` must expose exactly the model's params.

Pure functions — no app, no DB. Fixtures are defined locally (not in conftest)
so this file is self-contained.
"""
import pytest

from config import MODEL_CODES, DEFAULT_HYPERPARAMS
from services.hyperparam_models import (
    HYPERPARAM_MODELS,
    build_defaults,
    build_param_labels,
    build_param_notes,
    build_validation_schemas,
)
from services.hyperparam_validator import (
    VALIDATION_SCHEMAS,
    get_model_schema,
    validate_hyperparams,
)


# ── Coverage: every model_code is backed by a Pydantic model ────────────────

def test_every_model_code_has_a_pydantic_model():
    missing = [c for c in MODEL_CODES if c not in HYPERPARAM_MODELS]
    assert not missing, f"model_codes with no Pydantic model: {missing}"


def test_registry_has_no_extra_codes():
    extra = [c for c in HYPERPARAM_MODELS if c not in MODEL_CODES]
    assert not extra, f"HYPERPARAM_MODELS has codes not in MODEL_CODES: {extra}"


@pytest.mark.parametrize("code", MODEL_CODES)
def test_validate_empty_returns_model_defaults(code):
    """validate_hyperparams(code, {}) must equal the model's own defaults."""
    model_cls = HYPERPARAM_MODELS[code]
    expected = {
        name: field.get_default(call_default_factory=False)
        for name, field in model_cls.model_fields.items()
    }
    out = validate_hyperparams(code, {})
    assert out == expected
    # ...and the empty-payload result is exactly the derived defaults dict too.
    assert out == DEFAULT_HYPERPARAMS[code]


@pytest.mark.parametrize("code", MODEL_CODES)
def test_get_model_schema_keys_match_model_params(code):
    schema = get_model_schema(code)
    assert schema is not None, f"schema unexpectedly None for {code}"
    model_params = list(HYPERPARAM_MODELS[code].model_fields.keys())
    assert list(schema.keys()) == model_params


@pytest.mark.parametrize("code", MODEL_CODES)
def test_schema_entries_have_type_and_default(code):
    schema = get_model_schema(code)
    for param, entry in schema.items():
        assert entry["type"] in ("int", "float", "str", "bool"), (code, param, entry)
        assert "default" in entry, (code, param)


# ── Derived structures stay consistent with their builders ──────────────────

def test_validation_schemas_is_the_derived_one():
    assert VALIDATION_SCHEMAS == build_validation_schemas()


def test_defaults_match_config():
    assert DEFAULT_HYPERPARAMS == build_defaults()


def test_param_labels_cover_every_param():
    labels = build_param_labels()
    for code in MODEL_CODES:
        for name in HYPERPARAM_MODELS[code].model_fields:
            assert name in labels, f"{name} (in {code}) has no label"


def test_param_notes_cover_every_param():
    notes = build_param_notes()
    for code in MODEL_CODES:
        assert code in notes
        for name in HYPERPARAM_MODELS[code].model_fields:
            assert name in notes[code] and notes[code][name], (
                f"{code}.{name} has no note"
            )


# ── Round-trip: valid overrides accepted, bad values rejected ───────────────

def test_valid_override_is_accepted_and_coerced():
    out = validate_hyperparams("random_forest", {"n_estimators": "250", "max_depth": 20})
    assert out["n_estimators"] == 250 and isinstance(out["n_estimators"], int)
    assert out["max_depth"] == 20
    assert out["criterion"] == "gini"  # untouched default preserved


def test_out_of_range_value_raises():
    with pytest.raises(Exception) as exc:
        validate_hyperparams("random_forest", {"n_estimators": 99999})
    assert "n_estimators" in str(exc.value)


def test_below_min_value_raises():
    with pytest.raises(Exception):
        validate_hyperparams("k_means", {"n_clusters": 1})  # min is 2


def test_bad_enum_value_raises():
    with pytest.raises(Exception) as exc:
        validate_hyperparams("svm", {"kernel": "not-a-kernel"})
    assert "kernel" in str(exc.value)


def test_nullable_accepts_none_but_non_nullable_does_not():
    assert validate_hyperparams("random_forest", {"max_depth": None})["max_depth"] is None
    with pytest.raises(Exception):
        validate_hyperparams("random_forest", {"n_estimators": None})


def test_bool_string_coercion_matches_legacy_rule():
    # Legacy rule: only "true"/"1"/"yes" (case-insensitive) -> True; else False.
    assert validate_hyperparams("yolo", {"augment": "true"})["augment"] is True
    assert validate_hyperparams("yolo", {"augment": "TRUE"})["augment"] is True
    assert validate_hyperparams("yolo", {"augment": "yes"})["augment"] is True
    assert validate_hyperparams("yolo", {"augment": "1"})["augment"] is True
    assert validate_hyperparams("yolo", {"augment": "false"})["augment"] is False
    assert validate_hyperparams("yolo", {"augment": "0"})["augment"] is False
    assert validate_hyperparams("yolo", {"augment": "nonsense"})["augment"] is False
    assert validate_hyperparams("bert_finetune", {"freeze_base": "true"})["freeze_base"] is True
    assert validate_hyperparams("bert_finetune", {"freeze_base": "false"})["freeze_base"] is False


def test_unknown_params_are_ignored():
    out = validate_hyperparams("knn", {"totally_made_up": 7})
    assert "totally_made_up" not in out


def test_unknown_model_raises():
    with pytest.raises(Exception) as exc:
        validate_hyperparams("not_a_real_model", {})
    assert "Unknown model code" in str(exc.value)


def test_get_model_schema_unknown_returns_none():
    assert get_model_schema("not_a_real_model") is None
