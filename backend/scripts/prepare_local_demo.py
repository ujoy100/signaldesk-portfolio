"""Prepare missing local demo configuration without replacing existing secrets."""

import os
import secrets
from pathlib import Path


def prepare_local_demo(root: Path) -> dict[str, str]:
    """Create development-only files exclusively; leave existing files untouched."""
    files = {
        root / ".env": (root / ".env.example").read_bytes(),
        root / "frontend/.env": (root / "frontend/.env.example").read_bytes(),
        root / "secrets/postgres_password.txt": secrets.token_urlsafe(32).encode(),
        root / "secrets/auth_jwt_secret.txt": secrets.token_urlsafe(48).encode(),
    }
    results = {}
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        name = str(path.relative_to(root))
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            results[name] = "preserved"
            continue
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
        results[name] = "created"
    return results


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    for name, state in prepare_local_demo(root).items():
        print(f"{name}: {state}")
    print("Local demo only. Existing database volumes require their original password.")


if __name__ == "__main__":
    main()
