# Ground truth and replay evaluation

Run `uv run opspilot eval` from the repository root. The harness runs the same three investigations as the CLI and compares each report against [recorded expectations](../testbed/ground_truth/replay.json). The replay itself reads only telemetry. Keeping expected results outside the investigator lets you catch regressions when you change its implementation.

The harness checks the reported service, whether every claim cites an evidence record with a unique matching ID, whether expected measurements and events are cited, and whether a hypothesis is present when expected. For Payment, the expected behavior is to withhold a hypothesis. The scenario notes identify the injected cause, but the replay sees just one warning.

Citation resolution tells you the reader can find the cited record. To assess whether a claim is supported, check whether the source actually entails the claim. Finding an injected cause also requires a separate metric that compares the predicted cause with ground truth. Three passing replays measure behavior on these captures only.

## Practice

Copy `testbed/ground_truth/replay.json` to a temporary location and change the expected mean for the Ad fault window. Run `uv run opspilot eval --ground-truth PATH` with your copy. Find the failed check and the missing expected record. An automated build can use the nonzero exit status to detect that mismatch.

## Test the boundaries

The extended suite includes a healthy comparison, two equally timed candidate causes, a historical cutoff, and a captured Checkout-to-Payment incident. A healthy case tests false positives. A tie tests whether the agent preserves ambiguity. A cutoff tests look-ahead bias. The Checkout case checks measured failure counts and verifies each cited log-span pair by matching both identifiers.

Run `uv run opspilot eval --ground-truth testbed/ground_truth/extended.json` to see the checks. The healthy and ambiguity fixtures are synthetic. The Checkout case uses measured testbed traffic, which still covers only one controlled incident.
