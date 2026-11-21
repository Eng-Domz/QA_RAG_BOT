# API boundary

This directory is reserved for the production FastAPI application scheduled for
Week 2. The existing root Python modules remain the verified local CLI until
their domain behavior is extracted incrementally.

The API implementation must not begin by copying the CLI into a second codebase.
It will introduce validated settings, health/readiness/version endpoints, typed
request and response schemas, and adapters around the existing document and RAG
logic. See [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md).

No hosted API behavior is claimed by this scaffold.
