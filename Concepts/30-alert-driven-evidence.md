# Alert-driven evidence collection

An alert is a trigger and a time anchor. The webhook persists the alert's start time and queues the investigation. A worker uses that timestamp to query Prometheus. The ten-minute incident window ends at the alert start. The baseline runs from 25 to 15 minutes before the alert, with a five-minute gap between windows.

The operator configures the Prometheus endpoint and PromQL expression. The webhook selects a configured scenario through labels. It does not supply a destination or query. The expression must return one comparable percentage series for both windows.

The worker freezes the range responses under the investigation ID, then runs the same graph used for offline replay. A restarted worker can reuse that capture if it can read the same directory. This lets a report be audited after the monitoring system's retention window has moved on.

## Practice

Enable live capture for a local Ad alert. Watch for the `capture_prometheus` step in the event stream. Replay the saved file offline and compare the report with the API result.

## Capture a trace nominated by a Payment alert

A live Payment alert can carry a trace ID in the `opspilot_trace_id` annotation. The operator configures the Jaeger destination. The worker fetches the identified trace and checks for a failed Payment span before freezing it. An annotation can point to a trace retained by Jaeger, while the alert timestamp anchors resource-window queries in the other live path.

The report cites the failed span and its recorded parent. The presence of one failed trace gives request-level evidence. Impact assessment across all requests still needs a measured denominator.

If the worker can read an OpenTelemetry Collector file export, a Payment alert can also freeze its matching warning. The reader filters by trace ID and retains the source line and span ID. Replay can then prove that the warning was emitted in the particular failed span. If the configured log export is unavailable or has no matching warning yet, the report marks log coverage as partial and still cites Jaeger.

## Add aggregate failure rates

A Payment alert can also capture the configured Prometheus failure-rate series across baseline and incident windows. The arithmetic mean of the sampled percentages describes that time series. It can differ from failures divided by total requests across the whole window when traffic varies. Pair the aggregate evidence with a trace to describe both the observed rate and a specific failed operation.

## Discover a trace using an alert window

A service-level alert often has no request ID. OpsPilot searches Jaeger for
Payment spans in a bounded window before the alert, then checks that the
candidate actually contains a completed Payment error within the window. If
several traces qualify, the worker selects one deterministically by trace ID.
That trace illustrates a failed request. Metrics describe the request population.

The worker saves the trace before correlating logs by trace and span ID. A
retry uses the saved evidence. If the Jaeger search has no match and the
Prometheus query provides useful evidence, the report marks its coverage partial.

## Read span-derived request counters

The Collector counts spans by service, span kind, and status. Restricting the
query to Payment server spans measures requests at the Payment service boundary.
Including Checkout client spans would count some transactions twice. Prometheus
`rate()` estimates the per-second counter increase over the previous five
minutes. Dividing the error rate by the total rate gives the failure fraction
for that sampling point.

A missing error series can mean the service has recorded no errors. A missing
or zero total rate means there is no usable denominator at that point. The
example query supplies a zero numerator only where the total shows traffic.
