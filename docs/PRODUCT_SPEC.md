# Bilingual Knowledge Platform — Product Specification

## Purpose

The platform helps students turn Arabic and English study material into a
searchable knowledge workspace. A user uploads supported documents, asks a
question in Arabic or English, and receives an answer grounded in the uploaded
material with citations to the supporting passages.

The product is not intended to replace the source material or answer from the
model's general knowledge. Its main promise is evidence: when the documents do
not support an answer, the system should say so instead of inventing one.

## Problem

Students often have lecture notes, handouts, and reference material spread
across long files and two languages. Finding a particular explanation is slow,
ordinary keyword search misses paraphrases, and a general-purpose chatbot can
produce a confident answer that is not present in the course material.

The existing QA RAG Bot proves the core local retrieval workflow. This product
milestone turns that experiment into a multi-user, testable web application
without discarding the verified ingestion and grounding lessons.

## Target users

### Primary user

A university student who studies from Arabic, English, or mixed-language
documents and wants quick answers that can be checked against the source.

### Secondary user

A teaching assistant or study-group leader who wants to curate a private,
bounded knowledge collection and inspect where answers came from. Shared
collections are deferred until after the MVP.

## Core jobs to be done

1. Add a valid study document and understand whether processing succeeded.
2. Ask a question in Arabic or English without manually searching every file.
3. Verify an answer by opening its cited source passage.
4. Receive a clear refusal when the collection does not contain enough
   evidence.
5. Return later and continue using saved documents and conversations.

## Minimum viable user journey

1. The user signs in.
2. The user uploads a PDF, DOCX, TXT, or Markdown file.
3. The platform validates, extracts, chunks, embeds, and indexes the document.
4. The user sees a processing status and any actionable failure.
5. The user asks a question in Arabic or English.
6. The platform retrieves relevant chunks and either:
   - produces a grounded answer with citations; or
   - refuses because the evidence is insufficient.
7. The user opens a citation and checks the quoted passage and document name.

## MVP requirements

### Accounts and ownership

- Email-based sign-in and sign-out.
- Every document, conversation, and message belongs to one user.
- A user cannot read, search, update, or delete another user's content.

### Document ingestion

- Accept PDF, DOCX, TXT, and Markdown.
- Reject empty, unsupported, corrupt, duplicate, and oversized uploads with a
  useful message.
- Show uploading, processing, ready, and failed states.
- Preserve source name, page or section information when available, content
  hash, and processing timestamps.
- Make reprocessing idempotent so retrying does not create duplicate chunks.

### Retrieval and answers

- Support Arabic, English, and mixed-language questions.
- Retrieve a configurable number of chunks with scores and ownership filters.
- Apply a minimum evidence threshold before generation.
- Return an answer, language, citations, and request metadata in a structured
  response.
- Do not silently replace a provider error with an unsupported answer.
- Keep retrieval diagnostics available to the owner for evaluation and
  debugging, but hidden from the normal chat presentation.

### Web experience

- Responsive document workspace and chat interface.
- Correct right-to-left and left-to-right layout based on content language.
- Keyboard-accessible navigation, forms, dialogs, and citation controls.
- Clear empty, loading, success, refusal, quota, and error states.

### Operations

- Health, readiness, and version endpoints.
- Structured logs that exclude document contents, access tokens, and secrets.
- Application-level limits for upload size, documents, ingestion, and
  questions.
- Durable, atomic quota reservations before calling an external provider so
  simultaneous requests cannot bypass the free-demo limits.
- A public sample collection so the deployed demo remains useful without
  requiring visitors to upload content.

## Free-demo policy

The public portfolio deployment must remain usable at zero cost within provider
free tiers. Zero cost does not mean unlimited usage or a production uptime
guarantee.

- Do not configure an automatic paid fallback.
- Reject work when an application quota or provider quota is exhausted.
- Limit document size, page count, stored documents, and questions per user.
- Prefer a pre-indexed public sample collection for anonymous evaluation.
- Never send secrets or private application data to the browser.
- Require explicit acknowledgement before the first personal upload that the
  hosted free model path is for public or non-sensitive material only.
- Keep a local Ollama mode for private development and testing without hosted
  inference charges.

Exact limits will be recorded as configuration after provider accounts are
created and their current quotas are confirmed.

## Privacy promise for the demo

The free hosted embedding and generation tiers may process uploaded chunks,
submitted questions, and retrieved passages outside the application. Before a
first personal upload, the demo must name the configured providers, link their
current terms, explain which content crosses each boundary, and require the
user's acknowledgement. It must tell users not to upload employer-owned,
medical, regulated, confidential, or otherwise private documents.

Deleting a document must remove its active source object, chunks, and related
citations from application storage. The interface must also explain that
external-provider processing and backup retention are governed by the current
provider terms and might not be reversed by deleting the application copy. A
future production deployment would require an appropriate paid provider and
reviewed data-processing terms.

## Success criteria

These are targets for the first public release, not measurements already
achieved. Week 3 will create the evaluation set and establish the baseline.

| Area | Initial release target | How it will be measured |
|---|---:|---|
| Retrieval | Hit@5 at least 80% | At least 50 reviewed Arabic, English, and mixed-language questions |
| Citations | At least 90% citation correctness | Each cited passage must support the associated answer claim |
| Refusal | At least 85% correct refusal | Reviewed unanswerable and out-of-scope questions |
| Grounding | No unsupported material claims in the release evaluation | Manual claim-to-source review plus automated checks where practical |
| Warm latency | p95 answer time at most 10 seconds | Server timing from accepted question to complete response, excluding free-host cold starts |
| Reliability | All critical happy and failure paths pass | Automated API, ingestion, authorization, retrieval, and provider-failure tests |
| Coverage | At least 80% line coverage for backend application code | Coverage report in the verified local release gate or CI when available |
| Accessibility | No serious automated accessibility violations in core journeys | Automated scan plus keyboard-only review |
| Cost | $0 monthly for the bounded portfolio demo | Provider dashboards and hard application quotas |

Evaluation results must report dataset size, environment, model, embedding
model, thresholds, and date. A target that is not met must be reported as a
known limitation rather than presented as completed.

## Non-goals for the first release

- Unlimited public usage or guaranteed uptime.
- Enterprise compliance, private organization workspaces, or formal data
  residency guarantees.
- Answering from the open web or from model memory when documents lack evidence.
- OCR for scanned documents, handwriting recognition, audio, or video.
- Real-time collaborative editing.
- Training or fine-tuning a language model.
- Supporting every file format or every Arabic dialect equally.
- Replacing learning, instructors, or professional advice.

## Main risks and mitigations

| Risk | Effect | Initial mitigation |
|---|---|---|
| Weak Arabic or cross-language retrieval | Relevant evidence is missed | Use multilingual embeddings and a balanced bilingual evaluation set |
| Hallucinated answers | Users trust unsupported text | Evidence threshold, strict refusal, citations, and groundedness evaluation |
| Free-tier exhaustion | Demo temporarily stops answering | Per-user quotas, sample data, caching where justified, and fail-closed behavior |
| Free service cold starts | First request is slow | Explain demo status and measure warm and cold latency separately |
| Sensitive uploads | External provider receives private text | Prominent warning, bounded retention, deletion flow, and public samples |
| Cross-user data access | Privacy and security breach | Ownership filters, database row-level security, and authorization tests |
| Duplicate or partial ingestion | Incorrect retrieval and wasted storage | Stable hashes, idempotent jobs, transactions, and retry-safe status changes |
| Provider lock-in | Expensive rewrite when a free tier changes | Explicit generation and embedding provider interfaces |

## Release boundary

The MVP is complete only when a new user can sign in, upload a supported public
study document, receive a cited Arabic or English answer, observe a grounded
refusal, delete the document, and repeat the journey on the public demo. The
journey must be covered by proportionate automated tests and documented known
limitations.

