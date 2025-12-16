# Fomosto QSEIS Workflow for SeisComP

Simplified workflow for generating Green's Functions using Pyrocko/Fomosto and QSEIS, with conversion to SeisComP SC3GF1D format.

## Features

- **Simple YAML configuration** - No complex Python coding required
- **Automatic conversion** to SC3GF1D format for SeisComP
- **Multiple velocity models** supported (IASP91, AK135, PREM, custom)
- **Flexible configurations** - Regional, local, or teleseismic
- **Production-ready** - Tested with SeisComP moment tensor inversion

## Quick Start

### 1. Install Dependencies

```bash
# Install Pyrocko and Fomosto
pip install pyrocko

# Install ObsPy (for conversion)
pip install obspy

# Verify installation
./verify_install.sh
```

### 2. Install QSEIS Backend

```bash
# Initialize QSEIS backend
fomosto init qseis.2006b
```

Or copy pre-built `fomosto_qseis2006b` binary to your PATH.

### 3. Build Green's Functions

```bash
# Test with small configuration first
./build_small.sh

# Then build full production store
./build_full.sh
```

### 4. Convert to SC3GF1D Format

```bash
# Convert for SeisComP
python convert_to_sc3gf1d.py gf_stores/regional_8hz_2500km output_sc3gf1d

# This creates:
# - output_sc3gf1d/           (GF files in SC3GF1D format)
# - output_sc3gf1d.desc       (description file)
```

### 5. Use in SeisComP

```bash
# Copy to SeisComP GF directory
cp -r output_sc3gf1d/ $SEISCOMP_ROOT/share/greensfunctions/
cp output_sc3gf1d.desc $SEISCOMP_ROOT/share/greensfunctions/

# Configure scmtinv
scconfig
# Set: mtinv.greensFunctions = output_sc3gf1d
```

## File Descriptions

### Core Python Modules

- **`config_templates.py`** - Generate YAML configuration templates
- **`fomosto_wrapper.py`** - Simple wrapper around Fomosto CLI commands  
- **`velocity_models.py`** - Load and manage Earth velocity models
- **`convert_to_sc3gf1d.py`** - Convert Pyrocko GFs to SC3GF1D format

### Configuration Files

- **`test_small.yaml`** - Small test configuration (quick build)
- **`regional_8hz_2500km.yaml`** - Production regional configuration

### Build Scripts

- **`build_small.sh`** - Build test GF store
- **`build_full.sh`** - Build production GF store
- **`verify_install.sh`** - Check dependencies

## Configuration Parameters

Edit YAML files to customize:

```yaml
store_name: regional_8hz_2500km
earth_model: iasp91
sample_rate: 8.0

depth:
  min: 1.0
  max: 50.0
  delta: 1.0

distance:
  min: 10.0
  max: 2500.0
  delta: 10.0
```

## Scaling Factor

The conversion uses **1e15** scaling (line 462 in convert_to_sc3gf1d.py):

- **Pyrocko**: GFs normalized to 1 Nm  
- **SC3GF1D**: Requires 1e15 scaling
- **Verified**: Against working vendor GFs

## Documentation

- **[USAGE.md](USAGE.md)** - Detailed usage examples with correct fomosto commands
- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide

## References

- [Pyrocko/Fomosto](https://pyrocko.org/docs/current/apps/fomosto/tutorial.html)
- [SeisComP SC3GF1D](https://docs.gempa.de/mt/current/base/data.html#sc3gf1d)

---

**Version**: 1.0
**Date**: 2025-12-17
