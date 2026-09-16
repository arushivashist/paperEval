#!/usr/bin/env bash
# Downloads the real replication dataset (the repo ships a Git-LFS pointer stub).
# Source: CenterForOpenScience/llm-benchmarking (ReplicatorBench), study 16; also on OSF (osf.io/download/nkjsx).
set -e
cd "$(dirname "$0")/replication_data"
F="replicationDataset_Malik2020_with.year.csv"
SHA=072013f52649393612fd4a859b3fc52f7716791fe079d5df273c8df96afab1cd
if ! { [ -f "$F" ] && [ "$(shasum -a 256 "$F" | cut -d' ' -f1)" = "$SHA" ]; }; then
  curl -sL "https://media.githubusercontent.com/media/CenterForOpenScience/llm-benchmarking/main/replicatorbench/data/original/16/input/replication_data/$F" -o "$F"
fi
[ "$(shasum -a 256 "$F" | cut -d' ' -f1)" = "$SHA" ]
echo "B1 replication data present and checksum verified"
