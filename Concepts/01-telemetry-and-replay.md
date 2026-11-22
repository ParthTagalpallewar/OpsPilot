# Telemetry and deterministic replay

Telemetry is data a running system produces about its behavior. **Metrics** are numeric readings over time. **Logs** describe individual events. **Traces** link spans, which represent operations within a request. A metric can tell you CPU rose. A trace can show whether a request spent more time in an affected service during that rise.

From the repository root, run:

```sh
uv run opspilot replay ad-high-cpu
uv run opspilot replay email-memory-leak
```

## Read an evidence record

Open [the Ad fault capture](../testbed/scenarios/ad-stats-fault.csv) and match it to `ev_ad_fault_all`. The record includes the filename, resource metric, first and last timestamps, sample count, arithmetic mean and peak. A baseline uses the same metric on the same service during an earlier comparison window. The Ad baseline averages 0.74% CPU and the fault window averages 398.00%. Docker CPU percentages use one logical CPU as roughly 100%, so 398% corresponds to approximately four logical CPUs' worth of usage.

Email memory percentage uses the container memory limit as its denominator. The CLI keeps each fault variant's samples together, because pooling the samples would hide differences between windows. The arithmetic mean gives every reading equal weight. For irregular sampling that calls for a time-weighted estimate, measure how long each reading represents.

## Move from observation to hypothesis

The mean and peak describe measurements. OpsPilot emits a resource pressure hypothesis when each fault window's mean exceeds the baseline peak. This is a demo heuristic. A workload change can also elevate CPU or memory. Compare the resource windows with request latency, request volume, trace spans, and change events to test the explanation.

A frozen capture lets you rerun the tool on identical inputs. The same inputs produce the same evidence IDs and measurements. A testbed can record the injected cause independently and compare it with an investigator's output.

## Practice

1. Follow an observation's two evidence IDs and find their intervals and sample counts.
2. Compare the three Email variants. Identify which has the highest peak and explain why the variant label alone cannot predict observed memory use.
3. Copy the captures to a temporary directory. Use `--captures` to replay them after changing one percentage. Identify which summaries change and why.
