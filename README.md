# TaaS Monorepo

This repository is structured as a lightweight monorepo that can host the web frontend alongside multiple backend microservices.  The goal is to make it easy to plug in a Python backend (or any other service) without disturbing the existing React application.

## Repository layout

```
apps/
  frontend/        # React single page application
services/
  frontend-gateway/  # HTTPS gateway that serves the built frontend
```

Add new backend services under `services/` (for example `services/device-api/`) and keep shared infrastructure code or IaC templates under folders such as `infra/` if required.

## Frontend commands

Run the following commands from the repository root:

```bash
npm install --prefix apps/frontend
npm start --prefix apps/frontend
npm run build --prefix apps/frontend
npm test --prefix apps/frontend
```

## Frontend gateway

The HTTPS gateway that serves the compiled React build now lives in `services/frontend-gateway`.  Use it as the baseline for additional Node/Express microservices or replace it with your Python services as needed.

## Adding backend services

Create a new folder inside `services/` with its own dependencies and Dockerfile (if needed).  Each service can be developed, tested, and deployed independently, while the shared UI stays inside `apps/frontend`.
