#!/usr/bin/env bash
# Store the Gmail credentials the VPS uses to email you each edition for review, then send the latest one.
# Needs a Google app password (myaccount.google.com/apppasswords; requires 2-Step Verification).
# The password is read silently and piped straight to the VPS: never echoed, never in shell history or the repo.
set -euo pipefail
HOST=${HOST:-hoid}
read -rp "Gmail address to send from and to: " ADDR
read -rsp "Google app password (16 letters, spaces are fine): " PASS; echo
printf 'SMTP_USER=%s\nSMTP_PASSWORD=%s\nMAIL_TO=%s\n' "$ADDR" "${PASS// /}" "$ADDR" \
  | ssh "$HOST" 'install -d -m 700 /etc/aberdeen-daily && umask 077 && cat > /etc/aberdeen-daily/smtp.env'
unset PASS
ssh "$HOST" /usr/local/bin/aberdeen-daily-email --force
