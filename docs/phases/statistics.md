# Statistics

The API exposes profile statistics at `GET /api/profiles/{profile_id}/statistics`, with separate routes for improvement and milestones.

It excludes DNF and DNS records, then calculates total solves, best/worst time, overall mean, and means over the latest 5, 12, or 100 valid solves when enough records exist. Times are stored in milliseconds.

> **Important:** These are simple arithmetic means, not competition-style trimmed Ao5/Ao12 calculations. The dashboard currently shows local session data and is not connected to these endpoints.

Related code: `apps/api/services/statistics.py` and `apps/api/routes/statistics.py`. See [API Reference](../api.md).