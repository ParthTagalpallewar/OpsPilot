# Scenario: Payment Failure

## Setup
- Flag: `paymentFailure`
- Variant: <50% from /feature>
- Time flipped: 07:26:00:21/Nov/2026
- Load generator running: yes

## Timeline
- First symptom (first warn log): 2026-11-21 19:32:37
- Reverted (flag set to `off`): 2026-11-21 19:33:49
- Errors stopped: 2026-11-21 19:35:49

## Evidence
Check in Grafana Dashbaord in Demo -> Demo Dashboard -> Service (checkout, payment)
Record: 
2026-11-21 19:33:33
warn
Payment request failed. Invalid token. demo.user_context.loyalty_level=gold
default
namespace
record
@opentelemetry/instrumentation-pino
576dd3e4bb9e4697c36623d311477aeb2a61736abf97cfb329fd8cf5945803d3
docker-desktop
payment
nodejs

## Root cause
`payment` service, injected through the `paymentFailure` flag. The symptom appears in `checkout`, `payment` and `frontend`.


