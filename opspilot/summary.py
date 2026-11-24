"""Render a cited replay report as Markdown for incident channels and tickets."""

import re

MARKUP = re.compile(r"([\\`*_\[\]<>|#~])")
BULLET = re.compile(r"^([-+])")
NUMBERED = re.compile(r"^(\d+)([.)])")


def text(value) -> str:
    # Statements can quote telemetry or model output, so they stay on one line
    # and cannot open links, HTML, headings, lists, or table cells.
    escaped = MARKUP.sub(r"\\\1", " ".join(str(value).split()))
    return NUMBERED.sub(r"\1\\\2", BULLET.sub(r"\\\1", escaped))


def code(value) -> str:
    return f"`{str(value).replace('`', '')}`"


def citations(evidence_ids: list[str]) -> str:
    return ", ".join(code(evidence_id) for evidence_id in evidence_ids)


def hypothesis_lines(hypothesis: dict) -> list[str]:
    return [
        text(hypothesis["statement"]),
        "",
        f"- Confidence: {text(hypothesis['confidence'])}",
        f"- Recommended check: {text(hypothesis['recommended_check'])}",
        f"- Evidence: {citations(hypothesis['evidence_ids'])}",
    ]


def render_markdown(report: dict, *, title: str | None = None) -> str:
    lines = [
        f"# Incident report: {text(report['scenario'])} ({text(report['service'])})"
    ]
    if title:
        lines += ["", f"**Incident:** {text(title)}"]
    if report.get("as_of"):
        lines += ["", f"> Evidence visible as of {text(report['as_of'])}."]
    if report.get("coverage") == "partial":
        sources = ", ".join(
            f"{text(issue['source'])} ({text(issue['reason'])})"
            for issue in report.get("source_issues", [])
        )
        lines += ["", f"> Partial coverage. Unavailable sources: {sources}."]

    hypothesis = report["hypothesis"]
    lines += ["", "## Leading hypothesis", ""]
    if hypothesis is None:
        lines.append(
            "No hypothesis. The evidence does not support attributing a cause."
        )
    else:
        lines += hypothesis_lines(hypothesis)
    others = [item for item in report["hypotheses"] if item != hypothesis]
    if others:
        lines += ["", "## Other hypotheses", ""]
        lines += [
            f"- Rank {item['rank']}: {text(item['statement'])} "
            f"Evidence: {citations(item['evidence_ids'])}"
            for item in others
        ]

    sections = (
        ("Observations", report["observations"]),
        ("Runbook guidance", report.get("guidance", [])),
    )
    for heading, claims in sections:
        if claims:
            lines += ["", f"## {heading}", ""]
            lines += [
                f"- {text(claim['statement'])} ({citations(claim['evidence_ids'])})"
                for claim in claims
            ]

    explanation = report.get("model_explanation")
    if explanation is not None:
        lines += ["", "## Model explanation", ""]
        if explanation["status"] == "generated":
            lines.append(
                f"{text(explanation['statement'])} "
                f"({citations(explanation['evidence_ids'])}; "
                f"model {text(explanation['model'])})"
            )
        else:
            lines.append(f"Not generated: {text(explanation['status'])}.")

    lines += ["", "## Limitation", "", text(report["limitation"])]
    lines += ["", "## Evidence", "", "| ID | Kind | Source |", "|---|---|---|"]
    lines += [
        f"| {code(record['id'])} | {code(record.get('type') or record.get('metric'))} "
        f"| {code(record.get('source', '-'))} |"
        for record in report["evidence"]
    ]
    return "\n".join(lines) + "\n"
