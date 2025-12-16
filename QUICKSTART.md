# Quick Start Guide

## Three Ways to Build Your GF Store

### 1. Using the Build Script (Easiest)

```bash
cd /home/ubuntu/Projects/Dirk-gf/qseis-gf-generator/fomosto-workflow
./build_full.sh 8
```

This script will:
- Show configuration
- Ask for confirmation
- Build with timing
- Verify results automatically

### 2. Using the Wrapper

```bash
cd /home/ubuntu/Projects/Dirk-gf/qseis-gf-generator/fomosto-workflow
python3 fomosto_wrapper.py build regional_8hz_2500km --nworkers 8
```

### 3. Using Fomosto Directly

```bash
cd /home/ubuntu/Projects/Dirk-gf/qseis-gf-generator/fomosto-workflow/gf_stores/regional_8hz_2500km
fomosto build --nworkers 8 --force
```

## What You're Building

**Store:** regional_8hz_2500km
- **12,500 GFs** (250 distances × 50 depths)
- **125,000 traces** (10 components per GF)
- **~50-100 GB** storage required
- **~30-120 minutes** build time (8 workers)

## Quick Commands

```bash
# Check progress during build
cd gf_stores/regional_8hz_2500km
fomosto stats

# View results after build
fomosto view --extract='500k,@15'

# Generate PDF report
fomosto report

# Check for errors
python3 ../../fomosto_wrapper.py check regional_8hz_2500km

# Create decimated versions
fomosto decimate 2  # 4 Hz
fomosto decimate 4  # 2 Hz
```

## File Locations

```
Main directory:
/home/ubuntu/Projects/Dirk-gf/qseis-gf-generator/fomosto-workflow/

Configuration files:
├── test_small.yaml              (test config - COMPLETE)
└── regional_8hz_2500km.yaml     (full config - READY TO BUILD)

Store directories:
├── gf_stores/test_small_2hz/           (test store - COMPLETE)
└── gf_stores/regional_8hz_2500km/      (full store - READY TO BUILD)
```

## Monitor Build Progress

While building, you can check progress in another terminal:

```bash
cd /home/ubuntu/Projects/Dirk-gf/qseis-gf-generator/fomosto-workflow/gf_stores/regional_8hz_2500km
watch -n 10 'fomosto stats'
```

## After Building

1. **Verify integrity:**
   ```bash
   python3 fomosto_wrapper.py check regional_8hz_2500km
   ```

2. **Check statistics:**
   ```bash
   python3 fomosto_wrapper.py info regional_8hz_2500km
   ```

3. **Convert to SeisComP3** (if needed):
   ```bash
   cd /home/ubuntu/Projects/Dirk-gf/qseis-gf-generator
   python3 convert_to_sc3gf1d.py \
       fomosto-workflow/gf_stores/regional_8hz_2500km \
       gf_sc3gf1d/regional_8hz_2500km
   ```

## Need Help?

See full documentation:
- [README.md](README.md) - Complete workflow documentation
- [TEST_SUMMARY.md](TEST_SUMMARY.md) - Test results and details
