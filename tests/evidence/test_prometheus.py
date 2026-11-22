import io
import json
from unittest.mock import patch

from opspilot.evidence.prometheus import capture_comparison
from opspilot.replay import investigate


def test_prometheus_capture_can_replay_without_network(tmp_path):
    path = tmp_path / "ad-prometheus.json"

    def response(timestamp, value):
        return io.BytesIO(
            json.dumps(
                {
                    "status": "success",
                    "data": {
                        "resultType": "matrix",
                        "result": [
                            {
                                "metric": {"service": "ad"},
                                "values": [[timestamp, value]],
                            }
                        ],
                    },
                }
            ).encode()
        )

    with patch(
        "opspilot.evidence.prometheus.urlopen",
        side_effect=[
            response(1795305600, "2.0"),
            response(1795305900, "90.0"),
        ],
    ) as network:
        capture_comparison(
            "http://localhost:9090",
            "ad_cpu_percent",
            [
                "2026-11-22T00:00:00Z",
                "2026-11-22T00:02:00Z",
                "2026-11-22T00:05:00Z",
                "2026-11-22T00:07:00Z",
            ],
            30,
            path,
        )
    assert network.call_count == 2
    assert all(
        "/api/v1/query_range?" in call.args[0] for call in network.call_args_list
    )

    report = investigate("ad-high-cpu", tmp_path, with_claude=True)
    assert [item["mean"] for item in report["evidence"]] == [2.0, 90.0]
    assert report["evidence"][0]["query"] == "ad_cpu_percent"
    assert report["model_explanation"] == {"status": "capture_not_supported"}
