#!/bin/bash
set -e

# Collect all test nodeids
pytest --collect-only -q | grep '::' | awk '{print $1}' > test_list.txt

RESULTS=()
echo "\n=== Sequential Test Run Start ==="
while read -r test; do
  echo -e "\n=== Running $test ==="
  pytest -v "$test"
  RESULTS+=("$test:$?")
done < test_list.txt

echo -e "\n\n=== AGGREGATED RESULTS ==="
for r in "${RESULTS[@]}"; do
  echo $r
done

rm -f test_list.txt
