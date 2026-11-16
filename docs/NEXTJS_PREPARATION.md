# Next.js and TypeScript Preparation

This learning slice introduces the planned web interface without claiming that
the backend, upload flow, or model integration already exists.

## What was implemented

- A Next.js App Router project in `web/` using TypeScript, ESLint, and Tailwind.
- A server-rendered landing page with a focused interactive client boundary.
- Typed Arabic and English copy and right-to-left/left-to-right presentation.
- Typed `ready`, `processing`, and `failed` document states.
- Accessible status, progress, labels, focus styles, and reduced-motion support.
- Disabled upload and question controls that clearly identify the page as an
  interface prototype rather than simulating a completed backend.

## Concepts to understand

### Server and Client Components

`src/app/page.tsx` is a Server Component by default. It renders static product
content without adding that whole page to the browser's JavaScript bundle.

`src/app/components/study-workspace-preview.tsx` begins with `"use client"`
because the language switch uses React state and click handlers. The boundary
is intentionally small.

### Interfaces and unions

`Language` and `DocumentStatus` are string unions. They constrain the allowed
values instead of accepting any string. `DocumentSummary` defines the shape of
each document, including bilingual text and an optional processing percentage.

The `satisfies` operator checks that the copy and sample document data match
their contracts while preserving precise literal types. If a new unsupported
status or missing language is added, TypeScript reports it during development.

### Directionality

The preview derives `dir="rtl"` for Arabic and `dir="ltr"` for English. CSS
uses logical properties such as `border-inline-end`, so layout direction changes
without separate left/right styles.

### Expected states are data

Ready, processing, and failed are expected product states, not unexpected
exceptions. Modeling them explicitly makes the interface predictable and will
later let the FastAPI response schema and TypeScript UI agree on the same
contract.

## Commands

Run these from `web/`:

```powershell
npm run lint
npx tsc --noEmit
npm run build
npm run dev
```

The current page is a preparation milestone. Authentication, real document
upload, API calls, and generated answers remain future work.
