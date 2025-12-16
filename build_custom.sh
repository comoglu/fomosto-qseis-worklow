#!/bin/bash
#
# Build custom velocity model GF store
# Suitable for deeper events (e.g., Subduction zones)
#

set -e

CONFIG="custom_8hz.yaml"
STORE_DIR="gf_stores/custom_8hz_2500km"

echo "========================================================================"
echo "Building Custom Velocity Model GF Store"
echo "========================================================================"
echo "Configuration: $CONFIG"
echo "Output directory: $STORE_DIR"
echo ""
echo "Velocity Model (suitable for subduction zones):"
cat custom_model.tvel
echo ""
echo "Depth range: 1-150 km (for deeper events like in Subduction zones)"
echo "This will create 37,500 Green's Functions (150 depths × 250 distances)"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "Starting build..."
START_TIME=$(date +%s)

# Build the store
python fomosto_wrapper.py create $CONFIG
python fomosto_wrapper.py build $CONFIG

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
HOURS=$((ELAPSED / 3600))
MINUTES=$(((ELAPSED % 3600) / 60))
SECONDS=$((ELAPSED % 60))

echo ""
echo "========================================================================"
echo "Build complete!"
echo "Time elapsed: ${HOURS}h ${MINUTES}m ${SECONDS}s"
echo "========================================================================"
echo ""
echo "Verify the store:"
echo "  cd $STORE_DIR"
echo "  fomosto stats"
echo "  fomosto check"
echo ""
echo "Convert to SC3GF1D:"
echo "  python convert_to_sc3gf1d.py $STORE_DIR custom_8hz_sc3gf1d"
echo ""
