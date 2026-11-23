# Week 1 review

## Outcome

The existing QA RAG Bot now has a defined path from a verified local learning
project to a production-minded bilingual knowledge platform. The repository
keeps the working CLI intact while adding product, architecture, frontend, and
delivery boundaries incrementally.

## Completed evidence

- Audited and hardened the existing ingestion, retrieval, grounding, provider,
  configuration, and evaluation behavior with deterministic tests.
- Defined the bilingual platform's users, evidence-first promise, measurable
  targets, non-goals, privacy constraints, and free-demo policy.
- Documented the system context, trust boundaries, ingestion and question flows,
  application boundaries, initial data model, and rejected alternatives.
- Built a typed Next.js App Router prototype demonstrating component boundaries,
  responsive Arabic/English presentation, and accessible static states.
- Added reproducible Python 3.11 and Node.js 22 setup, locked frontend installs,
  contributor guidance, pre-commit checks, and a complete local verification
  command.
- Added CI for Python tests and frontend audit, lint, type-check, and production
  build. The clean-runner type failure was fixed and verified on `main`.

## Verified baseline

- The deterministic Python suite passes without API credentials or a running
  model.
- The frontend dependency audit, ESLint check, TypeScript check, and production
  build pass locally and in GitHub Actions.
- The default generation path is free and local through Ollama; hosted OpenAI is
  an explicit opt-in and cannot silently replace a missing local configuration.
- Current documentation distinguishes implemented CLI behavior from planned
  platform behavior.

These statements describe verified engineering checks, not user adoption,
production traffic, deployment uptime, or model-quality results.

## Decisions to explain without notes

1. **Why evolve instead of rewrite?** The existing project contains tested
   lessons about stable chunk identity, idempotent indexing, grounding, and
   provider failure. Incremental boundaries preserve that evidence.
2. **Why Next.js plus FastAPI?** Next.js provides the bilingual web experience;
   FastAPI creates an explicit Python boundary around document and RAG logic.
3. **Why PostgreSQL with pgvector later?** A multi-user product needs ownership,
   conversations, audit records, and vectors under transactional rules; local
   Chroma remains useful for the current CLI.
4. **Why separate health from readiness?** Health means the process is alive.
   Readiness means it can safely serve work with required dependencies available.
5. **Why explicit types over generated state?** A clean CI runner must not depend
   on files left behind by a developer's previous build.
6. **How does the demo stay free?** Use bounded free tiers, local Ollama for
   private development, no automatic paid fallback, and fail-closed quotas.

## Open risks entering Week 2

- Authentication, PostgreSQL persistence, row-level ownership, migrations, and
  object storage are designs, not implemented behavior.
- The current Python dependency generation is old and intentionally pinned; a
  compatibility upgrade needs its own tested change.
- No public deployment, uptime evidence, real-user feedback, or bilingual
  evaluation baseline exists yet.
- The API must adapt the verified domain behavior rather than duplicate CLI
  orchestration or initialize expensive models during import.

## Week 2 starting point

Day 8 introduces a lightweight FastAPI application factory with health,
readiness, version, and generated OpenAPI endpoints. The slice must remain
provider-free and deterministic so it can become the stable boundary for later
database, authentication, ingestion, and RAG features.
