# Local Compose secrets

Create `postgres_password.txt` and `auth_jwt_secret.txt` in this ignored directory.
Use development-only values. Never commit either file. Compose mounts them at runtime;
they are not copied into an image.

For a fresh public portfolio checkout, run this from the repository root:

```bash
python3 -m backend.scripts.prepare_local_demo
```

It creates only missing files, uses mode 0600, preserves existing credentials and
never prints their values. If you already have a database volume but lost its
password file, restore the original file first; do not generate a replacement.

Presence and ignore checks that do not reveal values:

```bash
test -s secrets/postgres_password.txt
test -s secrets/auth_jwt_secret.txt
git check-ignore -q secrets/postgres_password.txt
git check-ignore -q secrets/auth_jwt_secret.txt
```

PostgreSQL uses its password only when a volume is first initialized. If a named
volume already exists, changing the file does not change that database's password.
Restore the matching original development secret; do not delete the volume to force
a match. Backend services consume the same file through `DATABASE_PASSWORD_FILE`.
