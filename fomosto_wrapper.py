#!/usr/bin/env python3
"""
Minimal wrapper for Fomosto Green's Function workflow

This script provides a simplified interface to fomosto, handling:
- Store creation from YAML configs
- Automatic duration calculation
- Configuration validation
- Build management

Uses the standard fomosto CLI under the hood for maximum compatibility.

Usage:
    ./fomosto_wrapper.py create config.yaml
    ./fomosto_wrapper.py build store_name --nworkers 8
    ./fomosto_wrapper.py info store_name

Author: Simplified Fomosto workflow
"""

import sys
import argparse
import subprocess
import shutil
from pathlib import Path

try:
    from pyrocko import gf
    from pyrocko.fomosto import qseis
    import yaml
except ImportError:
    print("Error: Required packages not installed")
    print("Install with: pip install pyrocko pyyaml")
    sys.exit(1)

# Import velocity model utilities
from velocity_models import load_velocity_model


def calculate_optimal_duration(dist_max_km, depth_max_km, min_velocity_km_s=2.5):
    """
    Calculate optimal time window duration.

    Parameters:
    -----------
    dist_max_km : float
        Maximum distance in km
    depth_max_km : float
        Maximum source depth in km
    min_velocity_km_s : float
        Minimum expected velocity (default 2.5 km/s for surface waves)

    Returns:
    --------
    float : Recommended duration in seconds
    """
    # Time for slowest surface waves to arrive
    surface_wave_time = dist_max_km / min_velocity_km_s

    # Add time for multiple reflections and converted phases
    reflection_factor = 1.5
    depth_contribution = depth_max_km / 6.0

    # Total duration with safety margin
    duration = surface_wave_time * reflection_factor + depth_contribution + 100.0

    # Round up to nearest 100 seconds
    duration = ((int(duration) // 100) + 1) * 100

    # Minimum duration: 300s, Maximum practical: 3600s
    duration = max(300.0, min(duration, 3600.0))

    return duration


def validate_config(config):
    """Validate configuration and return warnings/errors"""
    warnings = []
    errors = []

    # Required fields
    required = ['store_name', 'earth_model', 'sample_rate', 'distance', 'depth']
    for field in required:
        if field not in config:
            errors.append(f"Missing required field: {field}")

    if errors:
        return warnings, errors

    dist_min = config['distance']['min']
    dist_max = config['distance']['max']
    dist_delta = config['distance']['delta']
    depth_max = config['depth']['max']
    sample_rate = config['sample_rate']

    # Distance validations
    if dist_min < 1.0:
        warnings.append(f"Distance minimum ({dist_min} km) < 1 km may cause issues")

    # Check distance sampling vs wavelength
    min_wavelength_km = 2.5 / sample_rate
    if dist_delta > min_wavelength_km / 2:
        warnings.append(
            f"Distance delta ({dist_delta} km) may undersample wavelengths "
            f"(min λ ≈ {min_wavelength_km:.1f} km)"
        )

    # Sample rate validations
    if sample_rate > 20.0:
        warnings.append(
            f"Sample rate ({sample_rate} Hz) > 20 Hz: "
            f"high storage requirements and computation time"
        )

    # Duration validation
    duration = config.get('duration', 'auto')
    if duration != 'auto':
        optimal_duration = calculate_optimal_duration(dist_max, depth_max)
        if duration < optimal_duration * 0.7:
            warnings.append(
                f"Duration ({duration}s) may be too short for {dist_max} km distance"
            )
            warnings.append(f"  Recommended: {optimal_duration}s or use 'auto'")

    return warnings, errors


def create_store(config_file, base_dir='gf_stores', force=False):
    """
    Create a Fomosto GF store from YAML configuration.

    Parameters:
    -----------
    config_file : str or Path
        Path to YAML configuration file
    base_dir : str
        Base directory for GF stores
    force : bool
        If True, delete existing store

    Returns:
    --------
    Path : Path to created store
    """
    # Load configuration
    print(f"Loading configuration from: {config_file}")
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    store_name = config['store_name']
    print("=" * 70)
    print(f"Creating Green's Function Store: {store_name}")
    print("=" * 70)

    # Validate configuration
    warnings, errors = validate_config(config)

    if errors:
        print("\nConfiguration Errors:")
        for error in errors:
            print(f"  - {error}")
        return None

    if warnings:
        print("\nConfiguration Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
        print()

    # Load earth model
    print(f"Loading earth model: {config['earth_model']}")
    earth_model = load_velocity_model(config['earth_model'])

    # Extract parameters
    sample_rate = config['sample_rate']
    dist_min = config['distance']['min'] * 1000.
    dist_max = config['distance']['max'] * 1000.
    dist_delta = config['distance']['delta'] * 1000.
    depth_min = config['depth']['min'] * 1000.
    depth_max = config['depth']['max'] * 1000.
    depth_delta = config['depth']['delta'] * 1000.

    # Calculate duration
    duration_config = config.get('duration', 'auto')
    if duration_config == 'auto':
        duration = calculate_optimal_duration(
            config['distance']['max'],
            config['depth']['max']
        )
        print(f"Auto-calculated duration: {duration}s")
    else:
        duration = float(duration_config)

    time_start = config.get('time_start', -50.0)
    receiver_depth = config.get('receiver_depth', 0.0)
    ncomponents = config.get('components', 10)

    # Statistics
    n_dist = int((dist_max - dist_min) / dist_delta) + 1
    n_depth = int((depth_max - depth_min) / depth_delta) + 1
    total_gfs = n_dist * n_depth

    print(f"Sample rate: {sample_rate} Hz")
    print(f"Distance: {config['distance']['min']}-{config['distance']['max']} km "
          f"(Δ={config['distance']['delta']} km, n={n_dist})")
    print(f"Depth: {config['depth']['min']}-{config['depth']['max']} km "
          f"(Δ={config['depth']['delta']} km, n={n_depth})")
    print(f"Duration: {duration} s (from {time_start} s)")
    print(f"Total GFs: {total_gfs:,}")
    print("=" * 70)

    # Create store path
    store_path = Path(base_dir) / store_name

    if store_path.exists():
        if force:
            print(f"Removing existing store: {store_path}")
            shutil.rmtree(store_path)
        else:
            print(f"\nError: Store already exists at {store_path}")
            print("Use --force to overwrite")
            return None

    # Ensure parent directory exists
    store_path.parent.mkdir(exist_ok=True, parents=True)

    # Create QSEIS configuration
    qsconf = qseis.QSeisConfig()
    qsconf.qseis_version = '2006b'

    # Time region
    qsconf.time_region = (gf.Timing(f'{time_start}'), gf.Timing(f'{duration}'))
    qsconf.cut = (gf.Timing(f'{time_start}'), gf.Timing(f'{duration}'))
    qsconf.wavelet_duration_samples = 0.001

    # QSEIS-specific settings
    qseis_config = config.get('qseis', {})
    qsconf.sw_algorithm = qseis_config.get('sw_algorithm', 0)
    qsconf.sw_flat_earth_transform = qseis_config.get('sw_flat_earth_transform', 1)

    slowness = qseis_config.get('slowness_window', [0.0, 0.0, 0.0, 0.0])
    qsconf.slowness_window = tuple(slowness)

    qsconf.wavenumber_sampling = qseis_config.get('wavenumber_sampling', 2.5)
    qsconf.aliasing_suppression_factor = qseis_config.get('aliasing_suppression', 0.1)

    print(f"QSEIS algorithm: {qsconf.sw_algorithm} (0=full wavefield)")
    print(f"Flat earth transform: {qsconf.sw_flat_earth_transform}")

    # Create store configuration
    modelling_code = config.get('modelling_code', 'qseis.2006b')

    store_config = gf.ConfigTypeA(
        id=store_name,
        ncomponents=ncomponents,
        sample_rate=sample_rate,
        receiver_depth=receiver_depth,
        source_depth_min=depth_min,
        source_depth_max=depth_max,
        source_depth_delta=depth_delta,
        distance_min=dist_min,
        distance_max=dist_max,
        distance_delta=dist_delta,
        earthmodel_1d=earth_model,
        modelling_code_id=modelling_code,
    )

    # Create store
    print("\nCreating store...")
    store_config.validate()
    gf.store.Store.create(str(store_path), config=store_config, extra={'qseis': qsconf})

    print("Creating travel time tables...")
    store = gf.store.Store(str(store_path), 'r')
    store.make_ttt()
    store.close()

    print("\n" + "=" * 70)
    print("Store created successfully!")
    print(f"Location: {store_path.absolute()}")
    print("=" * 70)

    return store_path


def build_store(store_path, nworkers=None):
    """
    Build Green's functions using fomosto.

    Parameters:
    -----------
    store_path : str or Path
        Path to GF store
    nworkers : int
        Number of parallel workers
    """
    store_path = Path(store_path)

    if not store_path.exists():
        # Try to find it in gf_stores
        alt_path = Path('gf_stores') / store_path
        if alt_path.exists():
            store_path = alt_path
        else:
            print(f"Error: Store not found: {store_path}")
            return False

    print(f"Building Green's functions: {store_path}")

    # Build command
    cmd = ['fomosto', 'build']
    if nworkers:
        cmd.extend(['--nworkers', str(nworkers)])

    print(f"Running: {' '.join(cmd)}")
    print("=" * 70)

    # Run in store directory
    try:
        subprocess.run(cmd, cwd=store_path, check=True)
        print("=" * 70)
        print("Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during build: {e}")
        return False
    except FileNotFoundError:
        print("Error: 'fomosto' command not found")
        print("Make sure Pyrocko is installed and fomosto is in your PATH")
        return False


def show_store_info(store_path):
    """Show store information using fomosto stats"""
    store_path = Path(store_path)

    if not store_path.exists():
        alt_path = Path('gf_stores') / store_path
        if alt_path.exists():
            store_path = alt_path
        else:
            print(f"Error: Store not found: {store_path}")
            return

    print(f"Store information: {store_path}")
    print("=" * 70)

    # Run fomosto stats
    try:
        subprocess.run(['fomosto', 'stats'], cwd=store_path, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
    except FileNotFoundError:
        print("Error: 'fomosto' command not found")


def check_store(store_path):
    """Check store for problems using fomosto check"""
    store_path = Path(store_path)

    if not store_path.exists():
        alt_path = Path('gf_stores') / store_path
        if alt_path.exists():
            store_path = alt_path
        else:
            print(f"Error: Store not found: {store_path}")
            return

    print(f"Checking store: {store_path}")
    print("=" * 70)

    try:
        subprocess.run(['fomosto', 'check'], cwd=store_path, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
    except FileNotFoundError:
        print("Error: 'fomosto' command not found")


def main():
    parser = argparse.ArgumentParser(
        description='Simplified Fomosto workflow wrapper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a store from config
  %(prog)s create my_config.yaml

  # Build with 8 workers
  %(prog)s build my_store --nworkers 8

  # Show store info
  %(prog)s info my_store

  # Check store for errors
  %(prog)s check my_store
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new GF store')
    create_parser.add_argument('config', help='YAML configuration file')
    create_parser.add_argument('--base-dir', default='gf_stores',
                              help='Base directory for stores')
    create_parser.add_argument('--force', action='store_true',
                              help='Overwrite existing store')

    # Build command
    build_parser = subparsers.add_parser('build', help='Build GFs for a store')
    build_parser.add_argument('store', help='Store name or path')
    build_parser.add_argument('--nworkers', type=int,
                             help='Number of parallel workers')

    # Info command
    info_parser = subparsers.add_parser('info', help='Show store information')
    info_parser.add_argument('store', help='Store name or path')

    # Check command
    check_parser = subparsers.add_parser('check', help='Check store for errors')
    check_parser.add_argument('store', help='Store name or path')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    if args.command == 'create':
        store_path = create_store(args.config, args.base_dir, args.force)
        if store_path:
            print("\nNext steps:")
            print(f"  {sys.argv[0]} build {store_path.name} --nworkers 8")
            return 0
        return 1

    elif args.command == 'build':
        success = build_store(args.store, args.nworkers)
        return 0 if success else 1

    elif args.command == 'info':
        show_store_info(args.store)
        return 0

    elif args.command == 'check':
        check_store(args.store)
        return 0

    return 0


if __name__ == '__main__':
    sys.exit(main())
