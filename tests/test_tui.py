from pathlib import Path

from midman.ai_backends import AIBackendConfig, configure_backend, resolve_ai_backend
from midman.connectors import ConnectorStatus
from midman.storage import load_backend_config, save_backend_config, save_profile_mapping
from midman.tui import _connector_status_badge, summarize_connector_counts


def test_summarize_connector_counts_groups_targets() -> None:
    connectors = [
        ConnectorStatus("srv01", "linux", "10.0.0.1:22", "ssh", "configured", "ssh", "rule-based-local"),
        ConnectorStatus("leaf01", "network", "10.0.0.2:22", "ssh", "configured", "ssh", "rule-based-local"),
        ConnectorStatus("idrac01", "management", "10.0.0.3:443", "https", "configured", "idrac", "rule-based-local"),
    ]

    counts = summarize_connector_counts(connectors)

    assert counts == {"linux": 1, "network": 1, "management": 1}


def test_configure_backend_updates_display_name() -> None:
    configure_backend("ollama", endpoint="100.123.179.111:11434", model="llama3.1")
    assert "ollama" in resolve_ai_backend()
    assert "100.123.179.111:11434" in resolve_ai_backend()


def test_backend_config_round_trip(tmp_path: Path) -> None:
    config = AIBackendConfig(provider="openai", endpoint="api.openai.com", model="gpt-5-mini", api_key="secret")
    save_backend_config(config, tmp_path)
    restored = load_backend_config(tmp_path)
    assert restored is not None
    assert restored.provider == "openai"
    assert restored.model == "gpt-5-mini"
    assert restored.api_key == "secret"


def test_save_profile_mapping_creates_profile_file(tmp_path: Path) -> None:
    path = save_profile_mapping(
        "macbook",
        {"name": "macbook", "type": "linux", "host": "192.168.1.50", "port": 22, "username": "ilan"},
        tmp_path,
    )
    assert path.exists()
    assert "macbook" in path.read_text()


def test_connector_status_badge_formats_known_states() -> None:
    assert _connector_status_badge("reachable")[0] == "[up]"
    assert _connector_status_badge("unreachable")[0] == "[down]"
    assert _connector_status_badge("configured")[0] == "[saved]"
