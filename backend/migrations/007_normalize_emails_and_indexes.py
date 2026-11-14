"""
Migration: lower-case stored emails, back-fill account fields, add indexes.

* Emails: login/signup now normalise to lower-case, so existing mixed-case
  rows are lower-cased here. A row is skipped (and reported) if lower-casing
  would collide with another account — those keep working through the
  case-insensitive fallback in authController.find_user_by_email.
* token_version: back-filled to 0 so session revocation ($inc) has a field.
* Indexes for the new / hotter query patterns:
    training_sessions (user_id, status, created_at) — concurrency cap + status filter
    training_sessions (user_id, model_code, version) — next-version lookup
    datasets (user_id, filename, version)           — latest-version lookup
    datasets (is_default, filename)                  — default library lookups
    pipelines (user_id, name) unique                 — one pipeline per name
    feedback (resolved, created_at)                  — admin inbox
    users (created_at), (last_login)                 — admin list + stats
"""


def _idx(coll, keys, name, unique=False):
    try:
        coll.create_index(keys, name=name, unique=unique)
    except Exception as e:  # noqa: BLE001
        print(f"    WARN: index {name} not created ({e})")


def up(db):
    changed = skipped = 0
    for u in db.users.find({"email": {"$type": "string"}}, {"email": 1}):
        email = u["email"]
        norm = email.strip().lower()
        if norm == email:
            continue
        if db.users.find_one({"email": norm, "_id": {"$ne": u["_id"]}}, {"_id": 1}):
            skipped += 1
            print(f"    WARN: not normalising {email!r}: another account already uses {norm!r}")
            continue
        db.users.update_one({"_id": u["_id"]}, {"$set": {"email": norm}})
        changed += 1

    db.users.update_many({"token_version": {"$exists": False}}, {"$set": {"token_version": 0}})

    _idx(db.training_sessions, [("user_id", 1), ("status", 1), ("created_at", -1)], "user_status_created")
    _idx(db.training_sessions, [("user_id", 1), ("model_code", 1), ("version", -1)], "user_model_version")
    _idx(db.datasets, [("user_id", 1), ("filename", 1), ("version", -1)], "user_filename_version")
    _idx(db.datasets, [("is_default", 1), ("filename", 1)], "default_filename")
    _idx(db.pipelines, [("user_id", 1), ("name", 1)], "uniq_user_pipeline", unique=True)
    _idx(db.feedback, [("resolved", 1), ("created_at", -1)], "resolved_created")
    _idx(db.users, [("created_at", -1)], "users_created_desc")
    _idx(db.users, [("last_login", -1)], "users_last_login")

    print(f"    Normalised {changed} email(s) ({skipped} skipped); added indexes")


def down(db):
    for coll, name in [
        (db.training_sessions, "user_status_created"),
        (db.training_sessions, "user_model_version"),
        (db.datasets, "user_filename_version"),
        (db.datasets, "default_filename"),
        (db.pipelines, "uniq_user_pipeline"),
        (db.feedback, "resolved_created"),
        (db.users, "users_created_desc"),
        (db.users, "users_last_login"),
    ]:
        try:
            coll.drop_index(name)
        except Exception:
            pass
