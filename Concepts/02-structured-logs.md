# Structured logs and evidence coverage

Run `uv run opspilot replay payment-failure` from the repository root. Find the warning in the report's evidence and follow its source filename and line number to the capture. The capture also records the original scenario note. Its timestamp preserves the reported wall time because the notes omit the timezone.

A JSON Lines file stores one JSON object per line. OpsPilot reads each record and groups warnings, errors, and fatal events by severity and exact message for the selected service. Exact grouping is easy to audit. When messages embed changing request IDs, a later ingestion step can group events by a trusted event name or a carefully normalized message template.

Severity describes how the application classified an event. In this case the service logged a failed request as a warning. A filter that searches only for errors would miss it. The text “Invalid token” is the recorded symptom. A request trace and a timeline of flag or deployment changes would help test the cause.

**A count needs a denominator to become a rate.** Suppose a complete capture contains 7 failed requests out of 15 requests in a defined interval. The rate is 7 ÷ 15, about 46.7%. For that calculation, use a verified total and count each failed request once even if it generated multiple warnings. The sample replay has one warning excerpt, so it emits a log count and leaves the cause unresolved.

## Practice

Copy the Payment fixture to a temporary directory and add a second identical line. Replay with `--captures` pointing to that directory. The cluster references two lines and its count becomes two. Explain what additional field you would need to tell whether the lines came from two requests.
