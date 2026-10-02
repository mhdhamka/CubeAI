# Statistics

The API exposes profile statistics at `GET /api/profiles/{profile_id}/statistics`, with separate routes for improvement and milestones.

It excludes DNF and DNS records, applies +2 penalties, and calculates total solves, best/worst time, and overall mean. Ao5 and Ao12 trim the best and worst results; Ao100 is the arithmetic mean of the latest 100 valid results. Times are stored in milliseconds.

The dashboard loads these aggregates from the API-backed profile and refreshes them after a solve is saved.

Related code: `apps/api/services/statistics.py` and `apps/api/routes/statistics.py`. See [API Reference](../api.md).