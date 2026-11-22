# 2026-11-22 · Evaluation traces and Langfuse export

Added evaluator spans for each frozen replay case. The spans carry aggregate checks, citation counts, and a reference dataset hash. They are linked to the underlying replay spans. Added an opt-in Langfuse OTLP mode with its project authentication and ingestion version header.

Verified the actual HTTP and protobuf export against a local receiver with dummy keys. The payload contained all three evaluator outcomes and excluded the dummy secret and source warning text. No hosted project was contacted. Langfuse UI ingestion and native experiment datasets remain unverified.

See the [evaluation tracing lesson](../Concepts/28-langfuse-evaluation-traces.md).
