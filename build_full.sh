#!/bin/bash
#
# Build script for the full regional_8hz_2500km GF store
#
# Usage:
#   ./build_full.sh [nworkers]
#
# Example:
#   ./build_full.sh 8    # Use 8 CPU cores
#

set -e

STORE_NAME="regional_8hz_2500km"
NWORKERS=${1:-8}

echo "=========================================="
echo "Building GF Store: $STORE_NAME"
echo "Workers: $NWORKERS"
echo "=========================================="
echo ""

# Check if store exists
if [ ! -d "gf_stores/$STORE_NAME" ]; then
    echo "Error: Store not found: gf_stores/$STORE_NAME"
    echo ""
    echo "Create it first with:"
    echo "  python3 fomosto_wrapper.py create regional_8hz_2500km.yaml"
    exit 1
fi

# Show store info
echo "Store configuration:"
echo "-------------------"
cd "gf_stores/$STORE_NAME"
head -n 25 config
echo ""

# Confirm before starting
echo "This will build approximately 12,500 GFs (125,000 traces)"
echo "Estimated size: 50-100 GB"
echo "Estimated time: 30-120 minutes with $NWORKERS workers"
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
echo "1. View waveforms: fomosto view --extract='500k,@15'"
echo "2. Generate report: fomosto report"
echo "3. Create decimated versions: fomosto decimate 2"
echo "4. Convert to SC3: python3 ../../convert_to_sc3gf1d.py . ../../gf_sc3gf1d/$STORE_NAME"
