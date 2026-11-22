# Change events and time correlation

Deployment records, feature flag updates, and configuration changes can explain why a service behaves differently after a particular time. Treat the change as its own evidence record with a service, a value, a source, and a time interval. An exact timestamp can be represented by identical earliest and latest times.

Run `uv run opspilot replay ad-high-cpu`. The last baseline reading was at 14:30:19 UTC and the first fault reading was at 14:31:25 UTC. The notes place the flag change somewhere in that 66-second gap. OpsPilot records the whole interval and cites it alongside the two metric summaries.

```text
last baseline reading                       first fault reading
14:30:19 UTC |====== documented change interval ======| 14:31:25 UTC
```

The correlator requires the entire change interval to fall between adjacent windows. This lets it claim that the interval is bracketed by the readings. A partial overlap leaves the timing ambiguous. A bracketed interval establishes ordering, and several changes can share the same gap. To evaluate causation, look for changes in request volume, compare traces across the transition, and check whether the symptoms recover after reversal.

## Practice

Replay Email and follow each change observation's three evidence IDs. Find the windows on either side of the switch to `1000x`. In a temporary copy of the capture, move the latest bound past the first reading of that window. Replay with `--captures` and check which observation disappears.
