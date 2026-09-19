# Deployment

**Site:** https://aberdeen-daily.technoir.cloud: Hostinger VPS (`ssh hoid`), Swarm service `aberdeen-daily` on `dokploy-network`, Traefik route `/etc/dokploy/traefik/dynamic/aberdeen-daily.yml`, Let's Encrypt.

The Dockerfile clones the vael-paper engine at a pinned commit, builds its reader, **fails the build if any edition has a mark** (`vael-paper-check --all`), exports the static site from `editions/`, adds `web/` (about page) and serves it with nginx.

```bash
./scripts/deploy.sh                                   # tests + edition check, build <sha> on the VPS, roll out, wait for /healthz
ssh hoid docker service rollback aberdeen-daily       # undo
```

**Email:** each edition becomes a Beehiiv draft in the "The Aberdeen Daily" publication. Sending stays a human action in Beehiiv.
