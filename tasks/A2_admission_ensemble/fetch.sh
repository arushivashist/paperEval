#!/usr/bin/env bash
# Downloads the CORE-Bench code capsule for this task into ./capsule
set -e
cd "$(dirname "$0")"
[ -d capsule ] && { echo "capsule already present"; exit 0; }
curl -L -o capsule.tar.gz https://corebench.cs.princeton.edu/capsules/capsule-0238624.tar.gz
mkdir -p capsule && tar -xzf capsule.tar.gz -C capsule --strip-components=1 && rm capsule.tar.gz
echo "fetched capsule-0238624"
