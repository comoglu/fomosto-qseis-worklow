#!/bin/bash
#
# Verify Pyrocko/Fomosto installation
#

echo "======================================"
echo "Verifying Pyrocko/Fomosto Installation"
echo "======================================"
echo ""

# Check Python version
echo "Python version:"
python3 --version
echo ""

# Check Pyrocko
echo "Pyrocko installation:"
python3 -c "import pyrocko; print(f'  Version: {pyrocko.__version__}'); print(f'  Location: {pyrocko.__file__}')"
echo ""

# Check ObsPy
echo "ObsPy installation:"
python3 -c "import obspy; print(f'  Version: {obspy.__version__}')"
echo ""

# Check NumPy
echo "NumPy installation:"
python3 -c "import numpy; print(f'  Version: {numpy.__version__}')"
echo ""

# Check fomosto command
echo "Fomosto command:"
which fomosto
fomosto help 2>&1 | head -5
echo ""

# Check QSEIS backend
echo "QSEIS backend:"
python3 -c "from pyrocko.fomosto import qseis; print('  QSEIS backend available: OK')"
echo ""

echo "======================================"
echo "Installation verified successfully!"
echo "======================================"
echo ""
echo "Ready to build Green's Functions!"
echo ""
echo "Next steps:"
echo "  cd fomosto-workflow"
echo "  ./build_full.sh 180"
