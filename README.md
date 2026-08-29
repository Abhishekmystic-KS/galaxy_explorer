# Galaxy Intelligence Platform

A web-based platform for exploring galaxies. Enter a galaxy name or coordinates to gather imaging + spectroscopic data, parse FITS, cross-match SIMBAD/NED, and generate interactive viewers + reports.

## Features
- Coordinate/Name lookup for galaxies.
- SQLite-backed background job queue with polling.
- FITS download and Astropy parsing.
- SIMBAD and NED cross-matching.
- Dynamic sky view using Aladin Lite v3.
- Spectrum plotting using Chart.js.
- Downloadable HTML reports and reproducible Matplotlib scripts.
- Rate limiting per IP.

## Installation
Ensure you have `uv` installed, then run:
```bash
uv sync
```

## Running the Server
```bash
uv run uvicorn app:app --reload
```

## Tests
```bash
uv run pytest
```

## CI/CD (GitHub Actions + Render)

This repository includes a GitHub Actions workflow at:
`/home/runner/work/galaxy_explorer/galaxy_explorer/.github/workflows/ci-cd.yml`

Pipeline behavior:
- On every push and pull request: installs dependencies, runs tests, and builds the Docker image.
- On pushes to `main`: triggers deployment to Render.

### Required secret for deployment
Add this repository secret in GitHub:
- `RENDER_DEPLOY_HOOK_URL`: your Render service deploy hook URL.
