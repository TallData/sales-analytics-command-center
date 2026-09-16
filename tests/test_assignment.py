import pytest

from src.assignment import confidence_band


@pytest.mark.parametrize(
    ("confidence", "expected"),
    [(0.95, "HIGH"), (0.90, "HIGH"), (0.899, "MEDIUM"), (0.70, "MEDIUM"), (0.69, "LOW")],
)
def test_confidence_band(confidence: float, expected: str) -> None:
    assert confidence_band(confidence) == expected


def test_confidence_band_rejects_invalid_value() -> None:
    with pytest.raises(ValueError):
        confidence_band(1.1)
