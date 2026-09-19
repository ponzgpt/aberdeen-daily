#!/usr/bin/env bash
# Install scripts/vps-autodeploy.sh on the VPS as a systemd timer (every 15 minutes). Idempotent.
set -euo pipefail
HOST=${HOST:-hoid}
cd "$(git rev-parse --show-toplevel)"
scp -q scripts/vps-autodeploy.sh "$HOST":/usr/local/bin/aberdeen-daily-autodeploy
ssh "$HOST" 'chmod +x /usr/local/bin/aberdeen-daily-autodeploy
cat > /etc/systemd/system/aberdeen-daily-autodeploy.service <<UNIT
[Unit]
Description=Deploy new commits of ponzgpt/aberdeen-daily
[Service]
Type=oneshot
ExecStart=/usr/local/bin/aberdeen-daily-autodeploy
UNIT
cat > /etc/systemd/system/aberdeen-daily-autodeploy.timer <<UNIT
[Unit]
Description=Check ponzgpt/aberdeen-daily for new editions every 15 minutes
[Timer]
OnBootSec=5min
OnUnitActiveSec=15min
[Install]
WantedBy=timers.target
UNIT
systemctl daemon-reload && systemctl enable --now aberdeen-daily-autodeploy.timer >/dev/null && systemctl start aberdeen-daily-autodeploy.service && systemctl list-timers aberdeen-daily-autodeploy.timer --no-pager | head -2'
