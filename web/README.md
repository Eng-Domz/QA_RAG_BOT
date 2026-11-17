# Dalil web interface

This directory contains the typed Next.js interface for the planned bilingual
knowledge platform.

The current milestone is deliberately an interface prototype. It demonstrates
the App Router, a small Server/Client Component boundary, typed document
states, accessible feedback, and Arabic/English direction changes. It does not
yet upload files, authenticate users, call the Python backend, or generate
answers.

## Local development

```powershell
npm install
npm run dev
```

Open <http://localhost:3000>.

## Verification

```powershell
npm audit --audit-level=high
npm run lint
npx tsc --noEmit
npm run build
```

See [`../docs/NEXTJS_PREPARATION.md`](../docs/NEXTJS_PREPARATION.md) for the
concepts this slice is intended to teach.
