import pytest

from midman.ai_parser import parse_intent


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("check linux server health", "linux_health"),
        ("show interface status on the core switch", "interface_status"),
        ("give me a bgp summary", "bgp_summary"),
        ("is the idrac reachable", "management_reachability"),
    ],
)
def test_parse_intent_maps_supported_requests(text: str, expected: str) -> None:
    parsed = parse_intent(text)
    assert parsed.action == expected
    assert parsed.confidence > 0.5


def test_parse_intent_rejects_unknown_request() -> None:
    with pytest.raises(ValueError):
        parse_intent("sing me a song")

