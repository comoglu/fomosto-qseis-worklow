# Usage Examples

## Test Store (test_small_2hz)

**Configuration:**
- Depths: 5, 15, 25 km (3 depths)
- Distances: 10, 30, 50, 70, 90 km (5 distances)
- Sample rate: 2 Hz
- Total GFs: 15 locations × 10 components = 150 traces

### Building

```bash
./build_small.sh
```

### Viewing GFs

**List all GFs:**
```bash
cd gf_stores/test_small_2hz
fomosto stats
```

**View specific GF:**
```bash
# Syntax: depth_index, distance_index
# Indices start at 0

# View depth=5km (index 0), distance=10km (index 0)
fomosto view --extract='0,0'

# View depth=5km (index 0), distance=30km (index 1)
fomosto view --extract='0,1'

# View depth=15km (index 1), distance=50km (index 2)
fomosto view --extract='1,2'

# View depth=25km (index 2), distance=90km (index 4)
fomosto view --extract='2,4'
```

**Valid index ranges:**
- Depth indices: 0-2 (for 5, 15, 25 km)
- Distance indices: 0-4 (for 10, 30, 50, 70, 90 km)

### Checking Store Info

```bash
cd gf_stores/test_small_2hz

# Store statistics
fomosto stats

# Store configuration
fomosto report

# Check completeness
fomosto check
```

## Production Store (regional_8hz_2500km)

**Configuration:**
- Depths: 1-50 km, 1 km steps (50 depths)
- Distances: 10-2500 km, 10 km steps (250 distances)
- Sample rate: 8 Hz
- Total GFs: 50 × 250 × 10 = 125,000 traces

### Building

```bash
./build_full.sh
```

### Viewing GFs

```bash
cd gf_stores/regional_8hz_2500km

# View depth=1km (index 0), distance=10km (index 0)
fomosto view --extract='0,0'

# View depth=10km (index 9), distance=100km (index 9)
fomosto view --extract='9,9'

# View depth=25km (index 24), distance=500km (index 49)
fomosto view --extract='24,49'

# View depth=50km (index 49), distance=2500km (index 249)
fomosto view --extract='49,249'
```

**Valid index ranges:**
- Depth indices: 0-49 (for 1-50 km)
- Distance indices: 0-249 (for 10-2500 km)

**Calculate indices:**
```python
# Depth index = (depth_km - depth_min) / depth_delta
# For depth=25km: (25 - 1) / 1 = 24

# Distance index = (distance_km - dist_min) / dist_delta  
# For distance=500km: (500 - 10) / 10 = 49
```

## Converting to SC3GF1D

### Test Store

```bash
python convert_to_sc3gf1d.py gf_stores/test_small_2hz test_small_sc3gf1d

# Output:
# - test_small_sc3gf1d/           (150 SAC files)
# - test_small_sc3gf1d.desc       (description file)
```

### Production Store

```bash
python convert_to_sc3gf1d.py gf_stores/regional_8hz_2500km regional_8hz_sc3gf1d

# Output:
# - regional_8hz_sc3gf1d/         (125,000 SAC files)
# - regional_8hz_sc3gf1d.desc     (description file)
```

### Conversion Options

```bash
# Skip zero traces (reduces file count)
python convert_to_sc3gf1d.py gf_stores/test_small_2hz output --skip-zeros

# Verbose output
python convert_to_sc3gf1d.py gf_stores/test_small_2hz output --verbose
```

## Verifying Output

### Check SAC Files

```bash
cd test_small_sc3gf1d

# List structure
ls -lh

# Check a specific file
saclst depmax depmin npts delta f 0050/00010/0050.00010.ZSS

# Or with ObsPy
python << EOF
from obspy import read
tr = read("0050/00010/0050.00010.ZSS")[0]
print(f"Samples: {tr.stats.npts}")
print(f"Delta: {tr.stats.delta}s")
print(f"Max amplitude: {tr.data.max():.3e}")
