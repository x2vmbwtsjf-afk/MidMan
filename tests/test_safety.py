from midman.safety import validate_action, validate_device_command, validate_user_text


def test_validate_user_text_blocks_shell_meta() -> None:
    decision = validate_user_text("show interfaces ; reload")
    assert not decision.allowed


def test_validate_user_text_blocks_write_language() -> None:
    decision = validate_user_text("delete the config backup")
    assert not decision.allowed


def test_validate_action_rejects_wrong_target() -> None:
    decision = validate_action("bgp_summary", "linux")
    assert not decision.allowed


def test_validate_device_command_only_allows_catalog_entries() -> None:
    decision = validate_device_command("linux_health", "uname -a")
    assert not decision.allowed

