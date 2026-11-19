import pytest
from opspilot.evidence.error_analysis import calculate_error_rate


@pytest.mark.parametrize(
    "total, failed, expected",
    [
        (1000, 100, 10.0),
        (100, 0, 0.0),
        (100, 100, 100.0),
        (0, 0, 0),
    ],
)
def test_calculate_error_rate(total, failed, expected):
    assert calculate_error_rate(total, failed) == expected
