#!/usr/bin/env bash
# Install the review email on the VPS: every day at 07:00 London time, email the latest edition once.
# Runs from systemd on the host, independent of the Hermes agent. Idempotent.
set -euo pipefail
HOST=${HOST:-hoid}
cd "$(git rev-parse --show-toplevel)"
scp -q scripts/email-edition.py "$HOST":/usr/local/bin/aberdeen-daily-email
ssh "$HOST" 'chmod +x /usr/local/bin/aberdeen-daily-email
cat > /etc/systemd/system/aberdeen-daily-email.service <<UNIT
[Unit]
Description=Email the latest Aberdeen Daily edition for review
[Service]
Type=oneshot
ExecStart=/usr/local/bin/aberdeen-daily-email
UNIT
cat > /etc/systemd/system/aberdeen-daily-email.timer <<UNIT
[Unit]
Description=Daily review email of The Aberdeen Daily
[Timer]
OnCalendar=*-*-* 07:00 Europe/London
Persistent=true
[Install]
WantedBy=timers.target
UNIT
systemctl daemon-reload && systemctl enable --now aberdeen-daily-email.timer >/dev/null && systemctl list-timers aberdeen-daily-email.timer --no-pager | head -2 && /usr/local/bin/aberdeen-daily-email'
