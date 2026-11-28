# Debug an OpsPilot investigation

Read the [architecture walkthrough](00-project-walkthrough.md) first. These
exercises use the saved examples and the Python environment in the Git checkout.
Run the commands from the repository root.

## Exercise 1. Follow the Ad CPU numbers

```sh
.venv/bin/python -m pdb .venv/bin/opspilot replay ad-high-cpu
```

At the debugger prompt, enter the following commands. Use `b` to stop at a
line, `c` to run until the next stop, `p` to print a value, and `q` to exit.

```text
b opspilot/replay.py:85
b opspilot/replay.py:199
b opspilot/replay.py:367
c
p state["captures"]
c
p [(r["phase"], r["mean"]) for r in state["windows"]]
c
p state["report"]["observations"][0]
p [(r["id"], r["source"]) for r in state["report"]["evidence"]]
q
```

The first stop shows the folder with saved inputs. The second shows the
calculated averages, 0.74% and 398%. The third shows the report and the
IDs it uses to point back to those inputs. Try explaining why the report
can measure the CPU spike directly but describes the flag as a possible cause.

## Exercise 2. Match a Payment log with a failed span

```sh
.venv/bin/python -m pdb .venv/bin/opspilot replay payment-failure \
  --captures testbed/captures/checkout-payment
```

```text
b opspilot/evidence/traces.py:212
c
p key
p trace["id"]
q
```

The two entries in `key` identify the whole request and one operation within
it. The matching trace record describes that same failed operation. The report
can cite the warning and span together while leaving the cause open.

## Exercise 3. Watch the worker receive a finished report

Follow the [API exercise](00-project-walkthrough.md#5-watch-the-api-and-worker-separately)
to start the API and submit a queued Ad CPU incident. Keep the API running.
Use the same database settings when starting the worker.

```sh
.venv/bin/python -m pdb -m opspilot.apps.worker.main --once
```

```text
b opspilot/investigations.py:239
c
p document["status"]
p report["observations"][0]
c
```

At the stop, the worker already has the report while the investigation is
still running. Continue, then fetch the investigation through the API using
the original ID. Check that it is completed and contains the report. This
path stores the report in the database. When you redirect the CLI replay,
the shell saves the printed report to the file you choose.

If line numbers move, use the first executable line inside
`collect_resource_evidence`, `report_resources`, `validate_report`,
`correlate_log_spans`, or `InvestigationStore._complete`.
