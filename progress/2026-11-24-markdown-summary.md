# 2026-11-24 · Markdown report summary

`opspilot replay SCENARIO --format markdown` and `GET /v1/investigations/{id}/summary` render a cited report as Markdown for an incident channel or ticket. Each statement keeps its evidence IDs, and the evidence table lists every cited record. Text that can come from telemetry, the incident title, or a model explanation is collapsed to one line and escaped, so it cannot add links, HTML, headings, lists, or table cells.

Verified with unit and API tests, including reader-role checks and a hostile-input case, a CommonMark rendering of hostile input that produced no links, images, HTML, or injected headings, and the smoke script's new `/summary` check. JSON output is byte-identical across every frozen scenario, capture, and evaluation.
