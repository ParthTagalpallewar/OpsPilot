# Historical replay and look-ahead bias

A historical replay answers a narrower question than a full replay. It asks what the captured evidence supports at a particular time. OpsPilot's `as_of` cutoff includes metric samples and timestamped logs at or before that instant. A change event appears once its entire recorded interval has elapsed. A span appears after its recorded end.

The baseline and incident summaries are computed from the remaining samples. If one window has no visible data, there is no comparison or hypothesis. Timestamped logs without a UTC offset are excluded because the replay cannot place them reliably on the timeline. Runbooks also lack historical versions, so time-bounded replays omit them.

This is a check against look-ahead bias in frozen data. Event timestamps can differ from when an operator first received the data. A production historical replay would also record availability timestamps and use versioned runbooks.

## Practice

Compare `uv run opspilot replay ad-high-cpu --as-of 2026-11-21T14:30:19Z` with the same command using `2026-11-21T14:31:25Z`. Count the evidence records in each report and identify what became visible.
