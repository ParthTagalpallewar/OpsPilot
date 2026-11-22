# Payment service operations

## Investigate Payment failures
For an invalid token warning, compare Payment and Checkout logs and trace the failing charge call. Review recent payment flag and deployment changes. Measure failures over a window using distinct failed requests divided by total requests.

## Verify Payment recovery
Compare the post-mitigation charge failure rate with the incident window. Confirm that checkout completes on an approved test transaction.
