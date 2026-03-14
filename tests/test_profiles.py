from pathlib import Path

from midman.profiles import list_profiles, load_profile


def test_load_profile_from_examples() -> None:
    profile = load_profile("sample-linux", base_path=Path.cwd())
    assert profile.type == "linux"
    assert profile.host == "192.0.2.10"


def test_list_profiles_discovers_examples() -> None:
    profiles = list_profiles(base_path=Path.cwd())
    names = {item.name for item in profiles}
    assert {"sample-linux", "sample-switch", "sample-idrac"} <= names

