#!/usr/bin/env bash
set -e; cd "$(dirname "$0")/.."; for f in tasks/A*/fetch.sh; do bash "$f"; done
