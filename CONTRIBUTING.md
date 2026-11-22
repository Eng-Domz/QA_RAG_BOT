# Contributing

This repository is evolving an independently built local RAG project into the
Dalil bilingual knowledge platform. Keep changes small, truthful, tested, and
easy to explain.

## Prerequisites

- Git
- Python 3.11
- Node.js 22 and npm
- Ollama only when manually testing local generation

## Windows setup

From the repository root:

```powershell
.\scripts\bootstrap.ps1
```

The script creates or updates `.venv`, installs Python development dependencies,
installs locked frontend dependencies, creates local environment files when
missing, and activates the version-controlled Git pre-commit hook. It never overwrites an existing
local environment file.

## Manual setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
cp .env.example .env
npm --prefix web ci
cp web/.env.example web/.env.local
git config core.hooksPath .githooks
```

## Verification

Windows contributors can run the complete local release gate:

```powershell
.\scripts\verify.ps1
```

The script checks Python dependencies, compilation and tests, then runs the npm
security audit, ESLint, TypeScript validation, and the Next.js production build.

## Working agreements

- Create a focused branch from an up-to-date `main`.
- Use conventional commit prefixes such as `feat:`, `fix:`, `test:`, `docs:`,
  `ci:`, `refactor:`, and `chore:`.
- Do not commit `.env`, `.env.local`, API keys, tokens, private documents,
  generated vector databases, or provider responses containing private data.
- Add or update tests when behavior changes. Include failure and ownership paths,
  not only successful requests.
- Do not claim an API, deployment, metric, or feature exists until it has been
  implemented and verified.
- Keep the current CLI working while the web platform is introduced
  incrementally.

## Pull requests

Explain the problem, the chosen boundary, the verification commands that actually
ran, known limitations, and anything a reviewer must reproduce manually. A failed
or unavailable external check must be documented rather than described as green.
