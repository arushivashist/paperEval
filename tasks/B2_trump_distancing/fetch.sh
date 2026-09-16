#!/usr/bin/env bash
# Downloads the real replication data (the repo ships Git-LFS pointer stubs).
# Source: CenterForOpenScience/llm-benchmarking (ReplicatorBench), study 1.
set -e
cd "$(dirname "$0")/replication_data"
BASE="https://media.githubusercontent.com/media/CenterForOpenScience/llm-benchmarking/main/replicatorbench/data/original/1/input/replication_data"
check() { # file sha256
  [ -f "$1" ] && [ "$(shasum -a 256 "$1" | cut -d' ' -f1)" = "$2" ]
}
check county_variables.csv 237b40f5ec9ba7ac1b8133e03770e7c310402c593efd80635d505ec1bd834a61 \
  || curl -sL "$BASE/county_variables.csv" -o county_variables.csv
check transportation.csv 261bd27abe0293fa7715c0d63571d4bc8bb96591f2ea829cbd37d2ff722327cd \
  || curl -L "$BASE/transportation.csv" -o transportation.csv
check county_variables.csv 237b40f5ec9ba7ac1b8133e03770e7c310402c593efd80635d505ec1bd834a61
check transportation.csv 261bd27abe0293fa7715c0d63571d4bc8bb96591f2ea829cbd37d2ff722327cd
echo "B2 replication data present and checksums verified"
