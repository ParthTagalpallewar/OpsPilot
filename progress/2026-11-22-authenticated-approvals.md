# 2026-11-22 · Reviewer authentication and attribution

Added optional bearer credentials with distinct operator, reviewer, and webhook roles. Protected investigation reads, the status stream, and evidence lookups alongside write routes when shared access is configured. Review events derive their principal from the credential. Same-review retries remain idempotent for the same principal.

Verified the authorization and audit flow at the ASGI boundary, including missing credentials, forbidden roles, attempted attribution from the request body, and competing reviewer retries. The local mode still labels reviews as local. Shared mode currently uses a static credential file. External identity provider integration remains pending.

See the [authenticated approvals lesson](../Concepts/26-authenticated-approvals.md).
