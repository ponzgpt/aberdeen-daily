# Deployment

**Site:** https://aberdeen-daily.technoir.cloud: Hostinger VPS (`ssh hoid`), Swarm service `aberdeen-daily` on `dokploy-network`, Traefik route `/etc/dokploy/traefik/dynamic/aberdeen-daily.yml`, Let's Encrypt.

The Dockerfile clones the vael-paper engine at a pinned commit, builds its reader, **fails the build if any edition has a mark** (`vael-paper-check --all`), exports the static site from `editions/`, adds `web/` (about page) and serves it with nginx.

```bash
./scripts/deploy.sh                                   # tests + edition check, build <sha> on the VPS, roll out, wait for /healthz
ssh hoid docker service rollback aberdeen-daily       # undo
```


## The daily edition (automatic)

- **Writer:** a scheduled task in the Claude desktop app on Javier's Mac ("The Aberdeen Daily — edición diaria", 06:00 London). It follows AGENTS.md, checks the edition, commits and pushes to `main`. It runs while the app is open; if the Mac is off, it runs at the next launch.
- **Publisher:** the systemd timer `aberdeen-daily-autodeploy.timer` on the VPS checks `main` every 15 minutes and rebuilds when it moved (`scripts/vps-autodeploy.sh`; reinstall with `scripts/install-autodeploy.sh`). The Docker build refuses an edition with marks, so the site keeps the last good paper.
- **Review copy:** the same task renders the live edition with `scripts/email-edition.py` and saves it as a Gmail draft to the editor. Beehiiv is paused.
