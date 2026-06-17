"""
Shared Flask extensions.

Instantiated WITHOUT an app so blueprints can import them (e.g. to apply
per-route rate limits) without importing app.py and creating a circular import.
app.py binds them with `limiter.init_app(app)` at startup.
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Global default limits apply to every route; sensitive routes (e.g. auth) add
# stricter per-route limits via @limiter.limit(...). Use a Redis storage_uri in
# production so limits are shared across workers and survive restarts.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["2000 per day", "500 per hour"],
    storage_uri="memory://",
)
