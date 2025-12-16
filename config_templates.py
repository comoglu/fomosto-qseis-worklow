#!/usr/bin/env python3
"""
Configuration templates for Fomosto GF stores

Provides simple YAML configuration generation for common scenarios.
These configs can be edited directly and used with the wrapper script.

Author: Simplified Fomosto workflow
"""

import yaml
from pathlib import Path


def create_regional_config(
    store_name='regional_8hz',
    earth_model='iasp91',
    sample_rate=8.0,
    distance_min=10.0,
    distance_max=1000.0,
    distance_delta=10.0,
    depth_min=1.0,
    depth_max=50.0,
    depth_delta=1.0
):
    """
    Create a configuration for regional seismology studies.

    Parameters:
    -----------
    store_name : str
        Name for the GF store
    earth_model : str
        Built-in model name or path to velocity model file
    sample_rate : float
        Sampling rate in Hz
    distance_min/max/delta : float
        Distance range in km
    depth_min/max/delta : float
        Source depth range in km

    Returns:
    --------
    dict : Configuration dictionary
    """
    return {
        'store_name': store_name,
        'earth_model': earth_model,
        'sample_rate': sample_rate,
        'distance': {
            'min': distance_min,
            'max': distance_max,
            'delta': distance_delta
        },
        'depth': {
            'min': depth_min,
            'max': depth_max,
            'delta': depth_delta
        },
        'duration': 'auto',  # Will be calculated automatically
        'time_start': -50.0,  # Pre-event time for stability
        'receiver_depth': 0.0,  # Surface receivers
        'components': 10,  # Full moment tensor
        'modelling_code': 'qseis.2006b',
        'qseis': {
            'sw_algorithm': 0,  # 0 = full wavefield (recommended)
            'sw_flat_earth_transform': 1,  # Apply flat earth transform
            'slowness_window': [0.0, 0.0, 0.0, 0.0],  # Full spectrum
            'wavenumber_sampling': 2.5,  # Wavenumber integration sampling
            'aliasing_suppression': 0.1,  # Anti-aliasing factor
        }
    }


def create_local_config(
    store_name='local_20hz',
    earth_model='crustal_model.txt',
    sample_rate=20.0,
    distance_max=200.0,
    depth_max=30.0
):
    """
    Create configuration for local studies (high frequency, short distance).
    """
    return {
        'store_name': store_name,
        'earth_model': earth_model,
        'sample_rate': sample_rate,
        'distance': {
            'min': 1.0,
            'max': distance_max,
            'delta': 1.0  # Fine sampling for local distances
        },
        'depth': {
            'min': 0.5,
            'max': depth_max,
            'delta': 0.5  # Fine depth sampling
        },
        'duration': 'auto',
        'time_start': -10.0,  # Shorter pre-event time
        'receiver_depth': 0.0,
        'components': 10,
        'modelling_code': 'qseis.2006b',
        'qseis': {
            'sw_algorithm': 0,
            'sw_flat_earth_transform': 1,
            'slowness_window': [0.0, 0.0, 0.0, 0.0],
            'wavenumber_sampling': 2.5,
            'aliasing_suppression': 0.1,
        }
    }


def create_teleseismic_config(
    store_name='teleseismic_2hz',
    earth_model='ak135-f-average',
    sample_rate=2.0,
    distance_max=10000.0,
    depth_max=100.0
):
    """
    Create configuration for teleseismic studies (low frequency, long distance).
    """
    return {
        'store_name': store_name,
        'earth_model': earth_model,
        'sample_rate': sample_rate,
        'distance': {
            'min': 100.0,  # Teleseismic distances
            'max': distance_max,
            'delta': 20.0  # Coarser sampling for long distances
        },
        'depth': {
            'min': 5.0,
            'max': depth_max,
            'delta': 2.0
        },
        'duration': 'auto',
        'time_start': -100.0,  # Longer pre-event time
        'receiver_depth': 0.0,
        'components': 10,
        'modelling_code': 'qseis.2006b',
        'qseis': {
            'sw_algorithm': 0,
            'sw_flat_earth_transform': 0,  # No flat earth for teleseismic
            'slowness_window': [0.0, 0.0, 0.0, 0.0],
            'wavenumber_sampling': 2.5,
            'aliasing_suppression': 0.1,
        }
    }


def save_config(config, filename):
    """
    Save configuration to YAML file.

    Parameters:
    -----------
    config : dict
        Configuration dictionary
    filename : str or Path
        Output filename
    """
    filepath = Path(filename)

    # Create directory if needed
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)

    print(f"Configuration saved to: {filepath}")
    return filepath


def load_config(filename):
    """
    Load configuration from YAML file.

    Parameters:
    -----------
    filename : str or Path
        Configuration file path

    Returns:
    --------
    dict : Configuration dictionary
    """
    with open(filename, 'r') as f:
        config = yaml.safe_load(f)
    return config


def main():
    """Create example configuration files"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate Fomosto configuration templates'
    )
    parser.add_argument('--type', choices=['regional', 'local', 'teleseismic'],
                       default='regional',
                       help='Type of configuration to generate')
    parser.add_argument('--output', '-o', default='gf_config.yaml',
                       help='Output filename')
    parser.add_argument('--store-name', help='Store name (overrides default)')
    parser.add_argument('--model', help='Earth model (overrides default)')
    parser.add_argument('--sample-rate', type=float, help='Sampling rate in Hz')

    args = parser.parse_args()

    # Create base config
    if args.type == 'regional':
        config = create_regional_config()
    elif args.type == 'local':
        config = create_local_config()
    else:  # teleseismic
        config = create_teleseismic_config()

    # Override with command line arguments
    if args.store_name:
        config['store_name'] = args.store_name
    if args.model:
        config['earth_model'] = args.model
    if args.sample_rate:
        config['sample_rate'] = args.sample_rate

    # Save configuration
    save_config(config, args.output)

    print("\nNext steps:")
    print(f"1. Edit the configuration file if needed: {args.output}")
    print(f"2. Create the GF store: ./fomosto_wrapper.py create {args.output}")
    print(f"3. Build GFs: ./fomosto_wrapper.py build {config['store_name']}")


if __name__ == '__main__':
    main()
