# Frontend Gateway Service

This lightweight Express service terminates TLS and serves the compiled React frontend from `apps/frontend/build`.

## Local development

```bash
npm install --prefix services/frontend-gateway
npm start --prefix services/frontend-gateway
```

Mount your TLS key and certificate into `/etc/tls/tls.key` and `/etc/tls/tls.crt` (or adjust `server.js`) before running the service.
