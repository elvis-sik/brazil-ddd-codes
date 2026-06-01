# AGENTS.md

## Scope

These instructions apply to this repository.

## Repo Goal

This repository is for building a high-quality Anki deck about Brazil's DDD telephone area codes.

Current focus:

- keep media provenance explicit
- derive reusable map assets programmatically from source SVGs when possible
- prefer outputs that stay fast inside Anki desktop and AnkiMobile
- prefer small, reviewable commits

## Git Hygiene

- Commit often when making meaningful progress.
- Push regularly once a remote exists.
- Sign all commits with GPG (`git commit -S`).

## Socket Firewall (`sfw`)

Always use [Socket Firewall Free](https://docs.socket.dev/docs/socket-firewall-free) when installing or fetching packages through supported public registries: prefix the command with `sfw` (for example `sfw npm install`, `sfw pnpm install`, `sfw yarn add`, `sfw pip install …`, `sfw uv pip install …`, `sfw cargo fetch`). It filters package-manager network traffic in real time and blocks confirmed malicious dependencies; no API key or configuration is required. Install the CLI globally with `npm i -g sfw` if it is not on your `PATH`. The free tier only supports public registries—not private or custom registries—so those installs cannot go through `sfw`; call that out explicitly if you must bypass it.

## Dependency versions: minimum age (7 days)

When adding dependencies, scaffolding a new package, or setting up a JS/Python project, configure the toolchain—**if it supports it**—so only releases **at least 7 days old** are eligible. This reduces risk from very fresh malicious publishes; it does not replace lockfiles, code review, or `sfw`.

- **npm** — Project root `.npmrc`: `min-release-age=7` (days). Verify with `npm config get min-release-age`; upgrade npm if the setting is unknown.
- **pnpm** — Workspace root `pnpm-workspace.yaml`: `minimumReleaseAge: 10080` (minutes = 7 days). Optional `minimumReleaseAgeExclude` for packages that must install immediately. Verify: `pnpm config get minimumReleaseAge`.
- **Yarn Berry** — Project root `.yarnrc.yml`: `npmMinimalAgeGate: 7d`. Optional `npmPreapprovedPackages` for exceptions. Verify: `yarn config get npmMinimalAgeGate`.
- **uv** — In `pyproject.toml`, `[tool.uv]` with `exclude-newer = "7 days"`. If you use `uv pip`, add the same under `[tool.uv.pip]`. Per-package overrides via `exclude-newer-package`. Optional machine-wide: `~/.config/uv/uv.toml` with `exclude-newer` and `[pip] exclude-newer`.

After changing policy: re-resolve dependencies, commit the lockfile, and in CI prefer frozen installs (`npm ci`, `pnpm install --frozen-lockfile`, `yarn install --immutable`). If a package manager has no equivalent, state that rather than inventing unsupported configuration.

