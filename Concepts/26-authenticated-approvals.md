# Authentication, authorization, and approval identity

Authentication identifies the caller. Authorization decides which operations the caller can perform. In shared mode, OpsPilot maps each bearer token to a configured principal and role. Operators can submit and read investigations, reviewers can read and decide, and webhook clients can submit Alertmanager notifications.

The approval endpoint attaches the authenticated principal to the stored event. This keeps attribution independent of the JSON body the caller sends. An immediate retry matches the saved decision only when it comes from the same principal.

For a local demonstration, the API can run without a credentials file and records reviews as `local`. A shared deployment can configure a credentials file, issue independent random tokens, and use HTTPS to protect those tokens in transit.

## Practice

Make one operator token and one reviewer token. Create an incident with the operator credential, attempt to approve it using the same credential, then approve it with the reviewer credential. Retrieve the investigation and trace the principal in its approval history.
