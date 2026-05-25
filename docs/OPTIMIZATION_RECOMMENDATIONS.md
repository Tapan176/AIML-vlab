# Optimization Recommendations

This document lists recommended improvements only. No changes from this document were applied as part of this pass.

## Highest Priority

- Move long-running training jobs out of Flask request threads and into a background worker system. The current backend streams training from request handlers, which makes web workers do double duty as training workers and increases timeout, scaling, and reliability risk.
- Replace the in-memory Flask-Limiter store with Redis or another shared backend in production. The current `memory://` setup is process-local, so limits will not be consistent across multiple instances.
- Stop running migrations on every application startup. Startup-time migrations add latency and create avoidable risk in horizontally scaled deployments.
- Add stronger MongoDB indexes for real query patterns. The current migrations only cover basic `user_id` and timestamp access, while the code frequently queries datasets by `user_id + filename + version` and sessions by user plus sort order.
- Store dataset previews instead of full `csv_data` blobs in MongoDB. Full CSV payloads inside documents will become expensive in storage, read time, and BSON size as datasets grow.

## Backend and Data Pipeline

- Add a compound index on `datasets(user_id, filename, version)` and another for default dataset lookup by `is_default + filename`.
- Add a compound index on `training_sessions(user_id, created_at)` and consider indexes for `status` and `model_code` if the UI keeps filtering by those fields.
- Add a unique index on `models.code` so the model metadata collection cannot drift into duplicate entries.
- Stream or chunk large CSV reads instead of loading full files eagerly for preview and processing when possible.
- Avoid base64-embedding large output images directly in JSON responses. Returning file URLs or dedicated download endpoints will reduce response size and memory pressure.
- Add cache invalidation and version-awareness to extracted ZIP datasets. Right now extracted image datasets can be reused from local cache without a strong freshness check against dataset version or Drive file identity.
- Parallelize or queue Google Drive uploads for model files and result zips. The current session finalization path performs these steps serially inside the request lifecycle.
- Add retry and backoff behavior around Drive uploads and deletions so transient cloud failures do not leave sessions in half-finished states.

## Model Runtime and ML Workflow

- Add lightweight preflight validation before training starts for dataset shape, label format, folder structure, and class count. Failing fast is much cheaper than discovering issues after a training job has already started.
- Revisit unconditional feature scaling for tree-based models. Decision trees, random forests, and boosted trees usually do not need scaling, so preprocessing can be simplified in those paths.
- Normalize training result payloads across models. Some routes return direct JSON, while deep models stream different event shapes; a shared contract would reduce frontend branching.
- Add dataset statistics caching so repeated training runs on the same dataset do not re-derive the same metadata each time.
- Consider configurable image preprocessing caches for CNN, ResNet, YOLO, and StyleGAN workloads to reduce repeated filesystem work on unchanged datasets.

## Frontend

- Replace repeated per-model `fetch` and `localStorage` patterns with a shared training hook or shared model form controller. The current model components duplicate a large amount of request, submit, and dataset-cache logic.
- Use the centralized `frontend/src/services/api.js` helper everywhere instead of mixing helper-based calls with raw `fetch`.
- Fix the upload flow in `ShowDataset.js`. `api.upload()` already returns parsed data, but the component still treats the returned value like a raw `fetch` response.
- Cache `/models/info` in a shared context or data store so model metadata is not refetched independently by each consumer.
- Add virtualization or pagination for large dataset previews so very large CSV tables or image lists do not expand the page cost linearly.

## Architecture and Operations

- Separate web-serving, training, and artifact-processing responsibilities into different worker roles. This will make scaling and failure handling much easier.
- Add structured logging with request IDs, session IDs, and model codes for easier debugging across SSE, training, upload, and DB flows.
- Define explicit retention and cleanup rules for uploaded datasets, extracted directories, result images, and temporary archives.
- Add health checks and observability around queue depth, Drive latency, training duration, and failed sessions.

## Maintainability

- Add tests that verify the canonical model catalog, validation schema, defaults, and exported Mongo JSON stay aligned.
- Add tests around frontend model forms to ensure the options exposed to users match backend validation rules.
- Consolidate repeated constants such as model codes, API paths, and dataset cache keys into shared definitions.
- Consider splitting the growing model metadata content into smaller source modules if the canonical catalog file becomes difficult to maintain.
