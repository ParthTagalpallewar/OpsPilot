"""Route incident text to a supported frozen demo scenario."""

import re

RULES = {
    "ad": ("ad-high-cpu", r"\b(?:ad|ads|getads)\b", r"\b(?:cpu|processor)\b"),
    "email": ("email-memory-leak", r"\b(?:email|e-mail)\b", r"\b(?:memory|heap|oom)\b"),
    "payment": (
        "payment-failure",
        r"\b(?:payment|payments|charge)\b",
        r"\b(?:fail\w*|error\w*|5\d{2}|invalid token)\b",
    ),
}


def route_incident(title: str, description: str, service: str | None = None) -> str:
    text = f"{title}\n{description}".lower()
    candidates = [
        scenario
        for name, (scenario, service_pattern, symptom_pattern) in RULES.items()
        if (service == name if service else re.search(service_pattern, text))
        and re.search(symptom_pattern, text)
    ]
    if len(candidates) == 1:
        return candidates[0]
    if candidates:
        raise ValueError("Multiple demo scenarios match. Supply a service or scenario.")
    raise ValueError(
        "No demo scenario matches. Supply a supported scenario explicitly."
    )
