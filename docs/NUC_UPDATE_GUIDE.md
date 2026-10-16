# NUC update guide (security cleanup release)

This release removes secrets and junk from git. It does **not** change how the
API, worker, database, or dashboard behave. One thing needs care on the NUC:

> When git stops tracking a file, the next `git pull` **deletes that file from
> the NUC's disk**. This release stops tracking `release/.env` (your real
> secrets) and `.venv/` (a Windows virtualenv that can't run on Ubuntu anyway).

Back up `release/.env` before pulling and put it back afterwards. From then on
it is ignored by git, so future pulls never touch it again.

The commands below assume the release compose setup. If the NUC uses a
different compose file or env file, swap in those paths.

```bash
cd ~/DroneInventoryManagmentSystem          # wherever the repo lives on the NUC
COMPOSE="docker compose -f release/docker-compose.release.yml --env-file release/.env"
```

## 1. Back up, pull, restore (required)

```bash
# 1a. Back up every local env file (copies live outside the repo)
cp release/.env ~/droneims-release.env.backup
[ -f .env ] && cp .env ~/droneims-root.env.backup

# 1b. Pull the update
git pull

# 1c. Put the env file back (git deleted it during the pull)
cp ~/droneims-release.env.backup release/.env
chmod 600 release/.env

# 1d. Check git now ignores it (should print the .gitignore rule)
git check-ignore -v release/.env
```

If you forget 1c, nothing is damaged: `docker compose up` refuses to start with
`Set POSTGRES_PASSWORD` / `Set JWT_SECRET_KEY` errors. Restore the file and run it again.

Database and MinIO data live in Docker volumes and are not touched by any of this.

## 2. Rebuild and restart

```bash
$COMPOSE up -d --build      # or your usual build/pull + up command
$COMPOSE ps                 # all services should become healthy
curl -fsS http://127.0.0.1:8000/ready
```

The backend image is now **smaller and faster to build**: YOLO/EasyOCR
(PyTorch) moved to the optional `requirements-vision.txt`. Nothing in the
running API used them.

## 3. Rotate the secrets that were public on GitHub

The old values are still in GitHub's history. Changing them makes the leaked
copies useless. All ports are bound to `127.0.0.1`, so only someone with access to
the NUC itself could have used them. That lowers the urgency, but rotating is
still the right move.

Generate new values:

```bash
openssl rand -hex 32    # for JWT_SECRET_KEY
openssl rand -hex 16    # for each password
```

### 3a. JWT_SECRET_KEY (safe, do this one)
Edit `release/.env`, replace `JWT_SECRET_KEY`, then `$COMPOSE up -d`.
Effect: everyone is logged out once and must log in again. No data impact.

### 3b. POSTGRES_PASSWORD (order matters)
Postgres stores the password inside its data volume. If you only change the env
file, the backend **can't connect**. Change it in the database first:

```bash
$COMPOSE exec postgres psql -U postgres -c "ALTER USER postgres WITH PASSWORD 'NEW_PASSWORD';"
# now set POSTGRES_PASSWORD=NEW_PASSWORD in release/.env, then:
$COMPOSE up -d
```

### 3c. MINIO_ROOT_PASSWORD
The backend uses the MinIO root user for S3 access (unless S3_ACCESS_KEY_ID is
set). Update `MINIO_ROOT_PASSWORD` in `release/.env` and recreate the stack with
`$COMPOSE up -d` so MinIO and the backend pick up the same value. Afterwards, open
a scan's evidence image in the dashboard to confirm downloads still work.
If anything fails, put the old value back from `~/droneims-release.env.backup`.

### 3d. Admin password from the old README
The old `create_superuser.py` never worked with this database, so that account
was never created in DroneIMS. **If you reused that password anywhere else**
(NUC login, GitHub, email), change it there.

To create a real admin account:

```bash
$COMPOSE exec backend python scripts/create_superuser.py --email you@example.com
```

## 4. Optional, non-destructive extra protection

- Make the GitHub repository **private** (GitHub → Settings → General → Danger
  Zone → Change visibility). The NUC then needs credentials to pull, e.g. a
  read-only deploy key: GitHub → Settings → Deploy keys.
- We deliberately did **not** rewrite git history. A history rewrite forces a
  force-push, which breaks `git pull` on the NUC. Rotating the secrets gives the
  same protection without that risk.
