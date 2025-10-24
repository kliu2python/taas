# Services Directory

Add each backend or supporting microservice inside this folder.  Every service should include:

- Its own `package.json`, `pyproject.toml`, or equivalent dependency manifest.
- Local development instructions.
- Dockerfile or deployment configuration if required.

Example layout:

```
services/
  frontend-gateway/   # serves the compiled React UI over HTTPS
  device-api/         # (example) Python FastAPI service for device orchestration
  results-worker/     # (example) background worker or cron service
```

Feel free to introduce additional folders such as `infra/` or `scripts/` at the repository root to support your deployment workflows.
