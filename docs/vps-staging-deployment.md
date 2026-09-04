# VPS Staging Deployment

This guide deploys wakiliDesk to the Ubuntu 22.04 VPS at `184.174.32.103` using Docker Compose and GitHub Actions.

The staging deployment is designed to coexist with other sites on the same VPS. wakiliDesk binds to `127.0.0.1:8085` by default, so it is not exposed publicly until Nginx proxies traffic to it.

Current staging hostname:

```text
https://staging.wakilidesk.com
```

DNS for `wakilidesk.com` is managed in Cloudflare. Hosting/proxy configuration is managed in Plesk on the VPS.

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
DJANGO_SECURE_PROXY_SSL_HEADER=true
ALLOWED_HOSTS=staging.wakilidesk.com,wakilidesk.com,184.174.32.103,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://staging.wakilidesk.com,https://wakilidesk.com
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
docker compose --env-file .env.prod -f docker-compose.prod.yml ps
curl -f http://127.0.0.1:8085/health/
```

Expected web binding when the staging domain is active:

```text
127.0.0.1:8085->8000/tcp
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
docker compose --env-file .env.prod -f docker-compose.prod.yml exec web python manage.py seed_dev
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

## 5. Cloudflare and Plesk Staging Domain

Because `wakilidesk.com` uses Cloudflare nameservers, public DNS records must be created in Cloudflare, not only in Plesk.

Cloudflare DNS records:

```text
Type: A
Name: staging
Content: 184.174.32.103
Proxy status: DNS only while issuing/testing Plesk SSL
TTL: Auto
```

Optional root records:

```text
Type: A
Name: @
Content: 184.174.32.103
Proxy status: DNS only

Type: CNAME
Name: www
Content: wakilidesk.com
Proxy status: DNS only
```

Confirm DNS:

```bash
dig +short staging.wakilidesk.com @8.8.8.8
dig +short staging.wakilidesk.com @1.1.1.1
dig +short NS wakilidesk.com @1.1.1.1
```

Expected:

```text
184.174.32.103
jen.ns.cloudflare.com.
malcolm.ns.cloudflare.com.
```

In Plesk:

1. Create `wakilidesk.com`.
2. Create `staging.wakilidesk.com`.
3. Set `staging.wakilidesk.com` to normal **Website hosting**, not **Forwarding**.
4. Issue a Let's Encrypt certificate for `staging.wakilidesk.com`.
5. Keep the app container bound to `127.0.0.1:8085`.

Do not use Plesk **Forwarding** to `http://127.0.0.1:8085`. Forwarding creates a browser redirect to localhost, which sends users to their own machine instead of reverse proxying to the VPS.

Working Plesk proxy file:

```bash
cd /var/www/vhosts/wakilidesk.com/staging.wakilidesk.com
nano .htaccess
```

Use:

```apache
Options -MultiViews
DirectoryIndex disabled

RewriteEngine On

RewriteCond %{REQUEST_URI} !^/\.well-known/acme-challenge/
RewriteRule ^(.*)$ http://127.0.0.1:8085/$1 [P,L,QSA]
```

If Plesk created a placeholder `index.html`, move it aside:

```bash
mv index.html index.html.bak
```

Confirm Apache proxy modules if the domain returns `500`:

```bash
apache2ctl -M | grep proxy
```

Required modules:

```text
proxy_module
proxy_http_module
rewrite_module
headers_module
```

Enable missing modules as `root`:

```bash
a2enmod proxy proxy_http rewrite headers
systemctl reload apache2
```

Confirm domain access:

```bash
curl -I https://staging.wakilidesk.com/health/
curl -I https://staging.wakilidesk.com/accounts/login/
curl -I https://staging.wakilidesk.com/documentation/
```

Expected health response:

```text
HTTP/2 200
content-type: application/json
```

Once HTTPS is stable in DNS-only mode, Cloudflare proxy can be enabled for the `staging` record. If enabling the orange-cloud proxy, set Cloudflare SSL/TLS mode to **Full (strict)**. Do not use **Flexible** SSL.

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

### Browser says `DNS_PROBE_FINISHED_NXDOMAIN`

Confirm the `staging` A record exists in Cloudflare. Plesk DNS entries do not control public DNS while the domain uses Cloudflare nameservers.

Check from Windows:

```powershell
Resolve-DnsName staging.wakilidesk.com -Server 8.8.8.8
Resolve-DnsName staging.wakilidesk.com -Server 1.1.1.1
```

Check from the VPS:

```bash
dig +short staging.wakilidesk.com @8.8.8.8
dig +short staging.wakilidesk.com @1.1.1.1
```

If Google DNS resolves but the local Windows resolver fails, flush local DNS and temporarily use Google DNS on the network adapter:

```powershell
ipconfig /flushdns
```

Use:

```text
Preferred DNS: 8.8.8.8
Alternate DNS: 8.8.4.4
```

Chrome Secure DNS can also cache a failing resolver. Set Chrome Secure DNS to Google Public DNS or disable it temporarily.

### Domain redirects to `https://127.0.0.1:8085/`

This means Plesk is configured as **Forwarding**, not as a reverse proxy.

Fix:

1. Change `staging.wakilidesk.com` hosting type to **Website hosting**.
2. Add the `.htaccess` proxy rules from section 5.
3. Move Plesk's placeholder `index.html` aside.

Confirm:

```bash
curl -I https://staging.wakilidesk.com/health/
```

The response must not include:

```text
Location: https://127.0.0.1:8085/
```

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

### Plesk rejects Additional nginx directives

Plesk may reject this:

```nginx
location / {
    proxy_pass http://127.0.0.1:8085;
}
```

Common errors:

```text
duplicate location "/"
"proxy_pass" directive is not allowed here
```

That means the Plesk directives field is not the right place for a root reverse proxy on this subscription. Use normal **Website hosting** plus the `.htaccess` proxy rules in section 5.
