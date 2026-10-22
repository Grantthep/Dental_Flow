# Staging deployment

Owned by Member 3 (Auth, DevOps & QA). Chosen 2026-10-18.

## What and why
One small Linux VPS (any provider: Hetzner, DigitalOcean, Vultr, AWS Lightsail, … ~US$5–6/month,
1–2 GB RAM) running **the same docker compose stack we use locally and in CI**, plus:

| Piece | What it does |
|---|---|
| `docker-compose.staging.yml` | override on top of `docker-compose.yml`: nothing but Caddy is exposed, containers restart on reboot |
| Caddy (`deploy/Caddyfile`) | HTTPS with automatic Let's Encrypt certificates; `/api/*` → FastAPI, everything else → Next.js |
| `backup` service | `pg_dump` once a day into `BACKUP_DIR`, keeps 14 days |
| `.github/workflows/deploy.yml` | after CI passes on `main`, SSHes in, checks out that commit, rebuilds, smoke-tests |

Why not a PaaS (Render/Railway/Fly): staging stays identical to what CI already tests, works on any
provider, no vendor config to learn, and the login rate limit sees real client IPs (backend trusts
`X-Forwarded-For` only from Caddy's fixed IP `172.30.0.10`).

## One-time server setup (whoever holds the cloud account)
1. Create an Ubuntu 24.04 VPS. Point a DNS **A record** (e.g. `staging.<your-domain>`) at its IP.
   No domain? A free subdomain from DuckDNS works.
2. Open ports 22, 80, 443 only (provider firewall or `ufw allow OpenSSH; ufw allow 80; ufw allow 443; ufw enable`).
3. Install Docker: `curl -fsSL https://get.docker.com | sh`
4. Deploy user + key for GitHub Actions:
   ```bash
   adduser --disabled-password --gecos "" deploy && usermod -aG docker deploy
   sudo -u deploy ssh-keygen -t ed25519 -N "" -f /home/deploy/.ssh/gha
   sudo -u deploy sh -c 'cat ~/.ssh/gha.pub >> ~/.ssh/authorized_keys'
   cat /home/deploy/.ssh/gha          # private key -> GitHub secret STAGING_SSH_KEY, then delete the file
   ```
5. Code and config:
   ```bash
   mkdir -p /opt/dentalflow /var/backups/dentalflow && chown deploy /opt/dentalflow /var/backups/dentalflow
   sudo -u deploy git clone https://github.com/Grantthep/Dental_Flow.git /opt/dentalflow
   cd /opt/dentalflow && sudo -u deploy cp .env.example .env && sudo -u deploy nano .env
   ```
   In `.env` set: `APP_ENV=staging`, a real `SECRET_KEY` (`python3 -c "import secrets; print(secrets.token_urlsafe(48))"`),
   a strong `POSTGRES_PASSWORD`, `DOMAIN=staging.<your-domain>`, `CORS_ORIGINS=https://staging.<your-domain>`,
   `BACKUP_DIR=/var/backups/dentalflow`, and a strong `SEED_PASSWORD` (staging is on the internet).
6. First start + demo data (synthetic only):
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d --build --wait
   docker compose -f docker-compose.yml -f docker-compose.staging.yml exec backend python seed.py
   ```
7. GitHub → repo **Settings → Environments → New environment `staging`**:
   - secrets: `STAGING_HOST` (server IP), `STAGING_USER` (`deploy`), `STAGING_SSH_KEY` (step 4),
     `STAGING_KNOWN_HOSTS` (output of `ssh-keyscan <server IP>` run from your own machine)
   - variable: `STAGING_DOMAIN` (`staging.<your-domain>`)

From then on every merge to `main` deploys automatically once CI is green. Manual redeploy:
**Actions → Deploy staging → Run workflow**. Until `STAGING_HOST` exists the deploy job just skips.

## Day to day
```bash
cd /opt/dentalflow
alias dc='docker compose -f docker-compose.yml -f docker-compose.staging.yml'
dc ps                    # status
dc logs -f backend       # logs
dc restart backend
```

## Backups and restore
Daily dumps land in `/var/backups/dentalflow/dentalflow-YYYYMMDD-HHMM.dump`. Copy them off the server
now and then (or turn on the provider's disk snapshots) — a backup on the same disk doesn't survive losing the server.

Restore (tested 2026-10-18):
```bash
dc stop backend frontend
dc exec backup sh -c 'dropdb dentalflow && createdb dentalflow && pg_restore -d dentalflow /backups/<file>.dump'
dc start backend frontend
```
