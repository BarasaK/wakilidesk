# VPS Staging Deployment

This guide deploys wakiliDesk to the Ubuntu 22.04 VPS at `184.174.32.103` using Docker Compose and GitHub Actions.

The staging deployment is designed to coexist with other sites on the same VPS. wakiliDesk binds to `127.0.0.1:8085` by default, so it is not exposed publicly until Nginx proxies traffic to it.

If you want to browse the app directly at `http://184.174.32.103:8085/` before a staging domain is ready, set `WAKILIDESK_HOST_BIND=0.0.0.0` in `.env.prod`, allow the port through the VPS firewall, and redeploy. Switch it back to `127.0.0.1` once Nginx is proxying the app.

## 1. GitHub Secrets

Configure these repository secrets:

```text
VPS_HOST=184.174.32.103
VPS_PORT=22
VPS_USER=deploy
VPS_APP_DIR=/opt/wakilidesk
VPS_SSH_KEY=<private deploy key>
```

If your SSH daemon uses a non-standard port, set `VPS_PORT` to that value.

## 2. VPS User

Create a non-root deploy user:

```bash
adduser deploy
usermod -aG docker deploy
mkdir -p /home/deploy/.ssh
nano /home/deploy/.ssh/authorized_keys
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys
```

Paste the public deploy key into `authorized_keys`.

After adding the user to the Docker group, log out and log back in before testing Docker commands as `deploy`.

## 3. First Server Checkout

Create the first checkout manually. This avoids giving GitHub Actions passwordless `sudo` access on a shared VPS.

As `root` or another sudo-capable user:

```bash
mkdir -p /opt/wakilidesk
chown deploy:deploy /opt/wakilidesk
```

Then as `deploy`:

```bash
git clone https://github.com/BarasaK/wakilidesk.git /opt/wakilidesk
cd /opt/wakilidesk
cp .env.prod.example .env.prod
nano .env.prod
```

Set strong production-style values:

```text
DJANGO_SECRET_KEY=<long random value>
DJANGO_DEBUG=false
ALLOWED_HOSTS=184.174.32.103,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://184.174.32.103
POSTGRES_PASSWORD=<strong database password>
WAKILIDESK_HOST_PORT=8085
WAKILIDESK_HOST_BIND=127.0.0.1
DEFAULT_FROM_EMAIL=wakilidesk@gmail.com
```

Generate a Django secret locally or on the VPS:

```bash
python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(50))
PY
```

## 4. Manual First Deployment

Run:

```bash
cd /opt/wakilidesk
chmod +x scripts/deploy.sh
APP_DIR=/opt/wakilidesk scripts/deploy.sh
```

Confirm services:

```bash
docker compose -f docker-compose.prod.yml ps
curl -f http://127.0.0.1:8085/health/
```

For temporary direct-IP staging access, update `.env.prod`:

```text
WAKILIDESK_HOST_BIND=0.0.0.0
WAKILIDESK_HOST_PORT=8085
ALLOWED_HOSTS=184.174.32.103,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://184.174.32.103:8085
```

Then redeploy:

```bash
APP_DIR=/opt/wakilidesk scripts/deploy.sh
```

If UFW is active, allow the staging port as `root` or another sudo-capable user:

```bash
ufw allow 8085/tcp
ufw status
```

Now test:

```bash
curl -f http://127.0.0.1:8085/health/
curl -f http://184.174.32.103:8085/health/
```

Optional for staging:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py seed_dev
```

Process due diary reminders manually:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml exec web python manage.py send_diary_reminders
```

For offline or early staging tests, keep email on the console backend:

```text
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=wakilidesk@gmail.com
```

For Gmail SMTP testing, use a Gmail app password:

```text
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=wakilidesk@gmail.com
EMAIL_PASSWORD=<gmail-app-password>
EMAIL_USE_TLS=true
DEFAULT_FROM_EMAIL=wakilidesk@gmail.com
```

Do not seed production pilot data unless this is intentionally a demo/staging environment.

## 5. Nginx Staging Proxy

Because the VPS hosts other sites, add this as a separate Nginx server block only when you have a staging hostname.

Example for `wakilidesk-staging.example.com`:

```nginx
server {
    listen 80;
    server_name wakilidesk-staging.example.com;

    client_max_body_size 50m;

    location / {
        proxy_pass http://127.0.0.1:8085;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and reload Nginx using your existing VPS convention. A common Ubuntu layout is:

```bash
sudo nano /etc/nginx/sites-available/wakilidesk-staging
sudo ln -s /etc/nginx/sites-available/wakilidesk-staging /etc/nginx/sites-enabled/wakilidesk-staging
sudo nginx -t
sudo systemctl reload nginx
```

When a domain and HTTPS are added, update `.env.prod`:

```text
DJANGO_SECURE_PROXY_SSL_HEADER=true
ALLOWED_HOSTS=wakilidesk-staging.example.com
CSRF_TRUSTED_ORIGINS=https://wakilidesk-staging.example.com
```

## 6. Automatic Deployments

After the first successful manual deployment, push to `master`.

GitHub Actions will:

1. SSH into the VPS.
2. Clone the repo if missing.
3. Fetch `origin/master`.
4. Reset the server checkout to `origin/master`.
5. Build Docker images.
6. Run migrations.
7. Collect static files.
8. Restart web and worker.
9. Run Django checks.

## 7. Rollback

To rollback manually:

```bash
cd /opt/wakilidesk
git log --oneline -5
git checkout <previous-good-commit>
APP_DIR=/opt/wakilidesk scripts/deploy.sh
```

To return to automatic deployment tracking:

```bash
git checkout master
git reset --hard origin/master
```

## 8. Notes

- `.env.prod` must never be committed.
- The staging compose file keeps Postgres and Redis off public host ports.
- The app listens on localhost only by default. Use `WAKILIDESK_HOST_BIND=0.0.0.0` only for temporary direct-IP staging access.
- Current MVP document storage uses the container media volume. Production pilots should move legal documents to private S3-compatible object storage with signed downloads.

## 9. Troubleshooting

### Browser says connection refused on `184.174.32.103:8085`

This usually means the app is either not running or is bound to localhost only.

Check the containers:

```bash
cd /opt/wakilidesk
docker compose --env-file .env.prod -f docker-compose.prod.yml ps
```

Check whether the app answers locally on the VPS:

```bash
curl -f http://127.0.0.1:8085/health/
```

If local curl works but the browser fails, either keep `WAKILIDESK_HOST_BIND=127.0.0.1` and configure Nginx, or set this for temporary direct access:

```text
WAKILIDESK_HOST_BIND=0.0.0.0
CSRF_TRUSTED_ORIGINS=http://184.174.32.103:8085
```

Then redeploy and confirm the firewall allows `8085/tcp`.
