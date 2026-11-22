# Human review and dry-run plans

A report explains what OpsPilot found. A plan describes a proposed follow-up check and cites the evidence behind it. When replay produces a hypothesis, the API includes a plan with an ID, a SHA-256 content hash, and a one-hour expiration.

The review request echoes both the ID and hash. This binds a decision to the version the reviewer saw. An edit creates a fresh plan and hash, so the revised text has its own review. The hash checks plan identity. In a shared service, authentication would establish who submitted the decision.

The store starts a write transaction before it reads the current plan and appends the decision. That sequence prevents two concurrent requests from both finalizing the same version. The history retains the reviewed plan, timestamp, decision, and any replacement plan. Approving records a decision on a dry-run check. The API has no command runner.

## Practice

Open the API docs and submit the Ad replay. Edit its proposed check, then try approving with the old plan ID and hash. Compare the conflict response with the result when you approve the revised version. Retrieve the investigation and follow both events in `approval_history`.

## Review output

An approval creates a saved dry-run preview in the same transaction as the reviewer event. It contains the reviewed plan ID, hash, action text, and cited evidence. The preview's executed-action list is empty. Edits issue a revised plan for review, and rejection ends the review without a preview.
