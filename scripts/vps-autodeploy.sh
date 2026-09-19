#!/usr/bin/env bash
# Runs on the VPS every 15 minutes (systemd timer, installed by scripts/install-autodeploy.sh).
# When main has a new commit (usually tonight's edition), build it and roll the service; the build
# itself refuses an edition with marks, so a bad edition never replaces a good one.
set -euo pipefail
APP=aberdeen-daily
SRC=/opt/$APP/src
[ -d $SRC/.git ] || git clone -q https://github.com/ponzgpt/aberdeen-daily.git $SRC
git -C $SRC fetch -q origin main
SHA=$(git -C $SRC rev-parse --short origin/main)
RUNNING=$(docker service inspect $APP -f '{{.Spec.TaskTemplate.ContainerSpec.Image}}' 2>/dev/null | sed 's/.*://; s/@.*//')
[ "$SHA" = "$RUNNING" ] && exit 0
git -C $SRC reset -q --hard origin/main
docker build -q -t $APP:$SHA $SRC >/dev/null
docker service update --quiet --no-resolve-image --image $APP:$SHA $APP
docker images $APP --format '{{.Tag}}' | tail -n +3 | xargs -r -I{} docker rmi $APP:{} >/dev/null 2>&1 || true
echo "deployed $APP:$SHA"
