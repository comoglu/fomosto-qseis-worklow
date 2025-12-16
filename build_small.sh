#!/bin/bash
#
# Build script for the small test GF store (test_small_2hz)
#
# Usage:
#   ./build_small.sh [nworkers]
#
# Example:
#   ./build_small.sh 4    # Use 4 CPU cores
#

set -e

STORE_NAME="test_small_2hz"
NWORKERS=${1:-4}

echo "=========================================="
echo "Building Small Test GF Store: $STORE_NAME"
echo "Workers: $NWORKERS"
echo "=========================================="
echo ""

# Check if store exists
if [ ! -d "gf_stores/$STORE_NAME" ]; then
    echo "Store not found. Creating it first..."
    echo ""
    python3 fomosto_wrapper.py create test_small.yaml --force
    echo ""
fi

# Show store info
echo "Store configuration:"
echo "-------------------"
cd "gf_stores/$STORE_NAME"
head -n 22 config
echo ""

# Confirm before starting
echo "This will build approximately 15 GFs (150 traces)"
echo "Estimated size: ~500 KB"
echo "Estimated time: <1 minute with $NWORKERS workers"
echo ""
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "=========================================="
echo "Starting build..."
echo "=========================================="
echo ""

# Start timer
START_TIME=$(date +%s)

# Build
fomosto build --nworkers=$NWORKERS --force

# End timer
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo ""
echo "=========================================="
echo "Build completed!"
echo "Time: ${MINUTES}m ${SECONDS}s"
echo "=========================================="
echo ""

# Show results
echo "Store statistics:"
fomosto stats

echo ""
echo "Checking for errors..."
fomosto check

echo ""
echo "=========================================="
echo "Success! Store is ready to use."
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. View waveforms: fomosto view --extract='50k,@10'"
echo "2. Convert to SC3: cd ../.. && python3 convert_to_sc3gf1d.py gf_stores/$STORE_NAME gf_sc3gf1d/$STORE_NAME"
echo "3. Build full store: cd .. && ./build_full.sh 8"
