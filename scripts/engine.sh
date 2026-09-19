#!/usr/bin/env bash
# Fetch the Vael Paper engine (checker, exporter, reader) at a pinned commit into .engine/ and set it up.
# Usage: scripts/engine.sh            -> prints the path of the engine's bin dir
set -euo pipefail
ENGINE_REPO=https://github.com/vaelkeep/vael-paper.git
ENGINE_REF=88b687a
cd "$(git rev-parse --show-toplevel)"
if [ ! -d .engine/.git ] || [ "$(git -C .engine rev-parse --short=7 HEAD)" != "$ENGINE_REF" ]; then
  rm -rf .engine && git clone -q "$ENGINE_REPO" .engine && git -C .engine checkout -q "$ENGINE_REF"
fi
[ -x .engine/.venv/bin/vael-paper-check ] || { python3 -m venv .engine/.venv && .engine/.venv/bin/pip install -q ./.engine/server; }
echo "$PWD/.engine/.venv/bin"
