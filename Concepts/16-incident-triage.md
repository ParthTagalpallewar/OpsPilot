# Incident triage and abstention

Triage decides which investigation to start. For local replay, OpsPilot looks for a supported service and a matching symptom in the incident title and description. “Payment API returning 500” matches Payment and its failure rule. Capture selection happens before evidence collection. The report then describes what the captured telemetry supports.

A service hint limits the rule to that service. When several scenarios match, the API returns HTTP 422 and asks for a service or scenario. When none match, it asks for an explicit scenario. An explicitly supplied scenario takes precedence over text routing.

Rules make routing reproducible. Their coverage depends on the vocabulary they recognize. A useful triage evaluation includes supported examples, unfamiliar wording, vague reports, and reports involving multiple services.

## Practice

Submit “Payment API returning 500” without a scenario. Then submit “Ad CPU and Email memory increased” with and without the Email service hint. Explain why the selected replay and its root-cause hypothesis are separate decisions.
