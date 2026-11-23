"""Import Deployment-owned ReplicaSet creation events into a frozen capture."""

import io
from csv import DictWriter
from pathlib import Path

from pydantic import AwareDatetime, BaseModel, Field

from opspilot.evidence.changes import CHANGE_FIELDS
from opspilot.evidence.snapshots import publish_snapshot

MAX_EXPORT_BYTES = 5_000_000


class Owner(BaseModel):
    kind: str
    name: str
    controller: bool = False


class ReplicaSetMetadata(BaseModel):
    name: str
    namespace: str
    created: AwareDatetime = Field(alias="creationTimestamp")
    owners: list[Owner] = Field(default_factory=list, alias="ownerReferences")
    annotations: dict[str, str] = Field(default_factory=dict)


class ReplicaSet(BaseModel):
    kind: str = "ReplicaSet"
    metadata: ReplicaSetMetadata


class ReplicaSetExport(BaseModel):
    items: list[ReplicaSet]


def import_rollouts(
    source: Path, directory: Path, *, namespace: str, deployment: str, service: str
) -> Path:
    if service not in {"ad", "email"}:
        raise ValueError("Rollout capture supports the Ad and Email resource scenarios")
    with source.open("rb") as stream:
        raw = stream.read(MAX_EXPORT_BYTES + 1)
    if len(raw) > MAX_EXPORT_BYTES:
        raise ValueError("ReplicaSet export exceeded the capture limit")
    try:
        export = ReplicaSetExport.model_validate_json(raw)
    except ValueError as exc:
        raise ValueError(f"{source}: invalid Kubernetes ReplicaSet export") from exc

    matches = []
    seen = set()
    for index, item in enumerate(export.items):
        meta = item.metadata
        if item.kind != "ReplicaSet" or meta.namespace != namespace:
            continue
        if not any(
            owner.controller and owner.kind == "Deployment" and owner.name == deployment
            for owner in meta.owners
        ):
            continue
        if meta.name in seen:
            raise ValueError(f"{source}: duplicate ReplicaSet {meta.name}")
        seen.add(meta.name)
        revision = meta.annotations.get("deployment.kubernetes.io/revision")
        value = f"ReplicaSet {meta.name} created"
        if revision and revision.isdecimal():
            value = f"revision {revision}, {value}"
        stamp = meta.created.isoformat()
        matches.append(
            (
                meta.created,
                meta.name,
                {
                    "kind": "deployment",
                    "name": f"{namespace}/{deployment}",
                    "value": value,
                    "earliest": stamp,
                    "latest": stamp,
                    "origin": f"{source.name}#/items/{index}/metadata",
                },
            )
        )

    if not matches:
        raise ValueError("No ReplicaSets are controlled by the selected Deployment")
    output = io.StringIO(newline="")
    writer = DictWriter(output, fieldnames=CHANGE_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(event for _, _, event in sorted(matches))
    path = directory / f"{service}-rollouts.csv"
    publish_snapshot(path, output.getvalue().encode())
    return path
