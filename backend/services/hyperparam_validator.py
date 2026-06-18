"""Hyperparameter validation for all ML models.

This module is now a thin compatibility layer over ``services.hyperparam_models``,
which holds the single Pydantic source of truth for every model's hyperparameters
(defaults, ranges, enums, nullability, labels, notes). The public surface is
unchanged:

* ``validate_hyperparams(model_code, user_params) -> dict``
* ``get_model_schema(model_code) -> dict | None``
* ``VALIDATION_SCHEMAS`` — derived from the models (kept for any importer/test),
  NOT hand-maintained.
"""
from services.hyperparam_models import (
    build_validation_schemas,
    get_model_schema,
    validate_hyperparams,
)


# Derived from the Pydantic models — do not hand-edit. Shape per param:
# ``{param: {'type': <python type>, 'min'?: , 'max'?: , 'options'?: ,
# 'nullable'?: True}}`` (same as the legacy hand-written dict).
VALIDATION_SCHEMAS = build_validation_schemas()


__all__ = ["VALIDATION_SCHEMAS", "validate_hyperparams", "get_model_schema"]
