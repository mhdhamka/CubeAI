# Deployment Notes

The checked-in Docker configuration is a development foundation, not a production deployment recipe. The Compose API entrypoint and bind mount need correction before the full stack can start reliably; see [Docker Status](Docker%20STATUS.md).

Before deploying:

- Replace all example credentials and keep secrets out of source control.
- Set `DEBUG=false` and restrict `CORS_ORIGINS` to the deployed web origin.
- Put the services behind HTTPS and configure WebSocket proxying if enabled.
- Add database migrations, backups, monitoring, and resource limits.
- Build and test the exact images and configuration used in deployment.

Do not expose PostgreSQL directly to the public internet. The default Compose port mapping is intended for local development.