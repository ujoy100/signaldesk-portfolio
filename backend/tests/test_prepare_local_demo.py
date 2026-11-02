"""Protect existing local credentials when preparing a recruiter demo."""

import stat
from pathlib import Path

from backend.scripts.prepare_local_demo import prepare_local_demo


def _templates(root: Path) -> None:
    (root / "frontend").mkdir()
    (root / ".env.example").write_text("APP_ENV=development\n")
    (root / "frontend/.env.example").write_text("VITE_ENABLE_DEV_LOGIN=true\n")


def test_preparation_creates_private_files_without_printing_secrets(tmp_path: Path):
    _templates(tmp_path)
    result = prepare_local_demo(tmp_path)
    assert set(result.values()) == {"created"}
    for name in result:
        path = tmp_path / name
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert path.read_bytes()
        assert path.read_text() not in str(result)
    assert (tmp_path / "secrets/postgres_password.txt").read_bytes() != (
        tmp_path / "secrets/auth_jwt_secret.txt"
    ).read_bytes()


def test_preparation_preserves_existing_configuration_and_credentials(tmp_path: Path):
    _templates(tmp_path)
    prepare_local_demo(tmp_path)
    paths = [tmp_path / name for name in prepare_local_demo(tmp_path)]
    before = {path: path.read_bytes() for path in paths}
    assert set(prepare_local_demo(tmp_path).values()) == {"preserved"}
    assert before == {path: path.read_bytes() for path in paths}


def test_preparation_does_not_follow_existing_secret_symlink(tmp_path: Path):
    _templates(tmp_path)
    external = tmp_path / "owner-secret"
    external.write_text("existing-owner-value")
    (tmp_path / "secrets").mkdir()
    (tmp_path / "secrets/postgres_password.txt").symlink_to(external)
    result = prepare_local_demo(tmp_path)
    assert result["secrets/postgres_password.txt"] == "preserved"
    assert external.read_text() == "existing-owner-value"
