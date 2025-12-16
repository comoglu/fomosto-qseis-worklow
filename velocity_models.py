#!/usr/bin/env python3
"""
Velocity model loading utilities for Fomosto GF generation

Supports:
- Built-in Pyrocko models (iasp91, ak135, prem)
- Custom velocity model files (.tvel, .nd, .m formats)
- Simple ASCII format

Author: Extracted from generate_gf_custom.py
"""

from pathlib import Path

try:
    from pyrocko import cake
except ImportError:
    print("Error: Pyrocko is not installed")
    print("Install with: pip install pyrocko")
    raise


def load_velocity_model(model_spec):
    """
    Load velocity model from various sources.

    Parameters:
    -----------
    model_spec : str
        Can be:
        - Built-in model name: 'iasp91', 'ak135-f-average', 'prem-no-ocean'
        - Path to .tvel file (travel time format)
        - Path to ND model file (.nd or .m format)
        - Path to simple ASCII file with layers

    Returns:
    --------
    cake.LayeredModel
    """
    model_path = Path(model_spec)

    # Try built-in models first
    builtin_models = {
        'iasp91': 'iasp91-compat.m',
        'ak135-f-continental': 'ak135-f-continental.m',
        'ak135-f-average': 'ak135-f-average.m',
        'ak135-f-oceanic': 'ak135-f-oceanic.m',
        'prem-no-ocean': 'prem-no-ocean.m',
        'prem-no-crust': 'prem-no-crust.m'
    }

    if model_spec in builtin_models:
        print(f"Loading built-in Pyrocko model: {model_spec}")
        try:
            model_file = builtin_models[model_spec]
            # Try to load using Pyrocko's builtin function
            try:
                return cake.load_model(model_file)
            except:
                # Fallback: construct path manually
                import pyrocko
                pyrocko_dir = Path(pyrocko.__file__).parent
                model_path = pyrocko_dir / 'data' / model_file
                if model_path.exists():
                    return cake.load_model(str(model_path))
                raise FileNotFoundError(f"Built-in model not found: {model_file}")
        except Exception as e:
            print(f"Error loading built-in model: {e}")
            print(f"Falling back to simple model for {model_spec}")
            return create_simple_model_for_builtin(model_spec)

    # Try loading from file
    if model_path.exists():
        print(f"Loading velocity model from file: {model_spec}")

        # Try .tvel format
        if model_spec.endswith('.tvel'):
            try:
                return load_tvel_model(model_path)
            except Exception as e:
                print(f"Error loading .tvel format: {e}")
                raise

        # Try ND format
        if model_spec.endswith('.nd') or model_spec.endswith('.m'):
            try:
                return cake.load_model(model_spec)
            except Exception as e:
                print(f"Error loading ND format: {e}")
                raise

        # Try simple ASCII format
        try:
            return load_simple_velocity_model(model_path)
        except Exception as e:
            print(f"Error loading velocity model: {e}")
            raise

    raise ValueError(f"Unknown model specification: {model_spec}")


def load_tvel_model(filepath):
    """
    Load velocity model from .tvel format.

    Format (.tvel files typically used with NonLinLoc/TauP):
        # Comments start with #
        depth(km) vp(km/s) vs(km/s) rho(g/cm3)
        OR
        depth(km) vp(km/s) vs(km/s)  (rho calculated from vp)

    Parameters:
    -----------
    filepath : Path
        Path to .tvel file

    Returns:
    --------
    cake.LayeredModel
    """
    model = cake.LayeredModel()

    depths = []
    materials = []

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            if len(parts) < 3:
                continue

            # Skip non-numeric lines (headers)
            try:
                depth_km = float(parts[0])
                vp_km_s = float(parts[1])
                vs_km_s = float(parts[2])
            except ValueError:
                continue

            # Density: either provided or estimated from Vp using Nafe-Drake
            if len(parts) >= 4:
                rho_g_cm3 = float(parts[3])
            else:
                # Nafe-Drake relation
                rho_g_cm3 = 1.6612 * vp_km_s - 0.4721 * vp_km_s**2 + \
                           0.0671 * vp_km_s**3 - 0.0043 * vp_km_s**4 + \
                           0.000106 * vp_km_s**5
                rho_g_cm3 = max(rho_g_cm3, 1.02)

            # Quality factors - use typical crustal/mantle values
            if depth_km < 35:  # Crust
                qp, qs = 600., 300.
            else:  # Mantle
                qp, qs = 1400., 600.

            # Handle velocity discontinuities
            if depths and abs(depth_km - depths[-1]) < 0.01:
                # Update last material (below discontinuity)
                materials[-1] = cake.Material(
                    vp=vp_km_s * 1000.,
                    vs=vs_km_s * 1000.,
                    rho=rho_g_cm3 * 1000.,
                    qp=qp,
                    qs=qs
                )
            else:
                depths.append(depth_km)
                materials.append(cake.Material(
                    vp=vp_km_s * 1000.,
                    vs=vs_km_s * 1000.,
                    rho=rho_g_cm3 * 1000.,
                    qp=qp,
                    qs=qs
                ))

    # Build layered model
    max_depth_km = 80  # Limit to upper mantle
    for i in range(len(depths) - 1):
        if depths[i] >= max_depth_km:
            break
        zbot = min(depths[i+1] * 1000., max_depth_km * 1000.)
        ztop = depths[i] * 1000.

        # Ensure layer has thickness
        if abs(zbot - ztop) < 1.0:
            continue

        model.append(cake.HomogeneousLayer(
            ztop=ztop,
            zbot=zbot,
            m=materials[i]
        ))

    # Last layer extends to 80 km
    if depths and len(depths) > 0:
        last_depth_m = min(depths[-1] * 1000., max_depth_km * 1000.)
        if last_depth_m < 80000:
            model.append(cake.HomogeneousLayer(
                ztop=last_depth_m,
                zbot=80000.,
                m=materials[-1]
            ))

    return model


def load_simple_velocity_model(filepath):
    """
    Load velocity model from simple ASCII format.

    Format (one layer per line):
        # Comments start with #
        depth_top(km) depth_bot(km) vp(km/s) vs(km/s) rho(g/cm3) qp qs

    Use depth_bot=0 for half-space

    Example:
        0.0   2.0  5.5  3.2  2.6  600  300
        2.0   10.0 6.2  3.6  2.8  600  300
        10.0  30.0 6.8  3.9  2.9  600  300
        30.0  0    8.1  4.5  3.3  1400 600  # Half-space

    Parameters:
    -----------
    filepath : Path
        Path to ASCII model file

    Returns:
    --------
    cake.LayeredModel
    """
    model = cake.LayeredModel()

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            if len(parts) < 7:
                continue

            ztop, zbot, vp, vs, rho, qp, qs = map(float, parts[:7])

            # Convert to meters and kg/m^3
            ztop_m = ztop * 1000.
            zbot_m = zbot * 1000. if zbot > 0 else None

            mat = cake.Material(
                vp=vp * 1000.,
                vs=vs * 1000.,
                rho=rho * 1000.,
                qp=qp,
                qs=qs
            )

            if zbot_m is None or zbot_m > 100000.:
                # Half-space (limit to 100 km)
                zbot_m = 100000.

            model.append(cake.HomogeneousLayer(
                ztop=ztop_m,
                zbot=zbot_m,
                m=mat
            ))

    return model


def create_simple_model_for_builtin(model_name):
    """
    Create simplified version of standard Earth models.

    Parameters:
    -----------
    model_name : str
        Name of built-in model (iasp91, ak135, prem)

    Returns:
    --------
    cake.LayeredModel
    """
    model = cake.LayeredModel()

    if model_name == 'iasp91':
        # Simplified IASP91
        model.append(cake.HomogeneousLayer(
            ztop=0., zbot=20000.,
            m=cake.Material(vp=5800., vs=3360., rho=2720., qp=600., qs=300.)
        ))
        model.append(cake.HomogeneousLayer(
            ztop=20000., zbot=35000.,
            m=cake.Material(vp=6500., vs=3750., rho=2920., qp=600., qs=300.)
        ))
        model.append(cake.HomogeneousLayer(
            ztop=35000., zbot=80000.,
            m=cake.Material(vp=8040., vs=4470., rho=3320., qp=1400., qs=600.)
        ))

    elif model_name.startswith('ak135'):
        # Simplified AK135
        model.append(cake.HomogeneousLayer(
            ztop=0., zbot=20000.,
            m=cake.Material(vp=5800., vs=3460., rho=2720., qp=600., qs=300.)
        ))
        model.append(cake.HomogeneousLayer(
            ztop=20000., zbot=35000.,
            m=cake.Material(vp=6800., vs=3900., rho=2920., qp=600., qs=300.)
        ))
        model.append(cake.HomogeneousLayer(
            ztop=35000., zbot=80000.,
            m=cake.Material(vp=8110., vs=4491., rho=3371., qp=1400., qs=600.)
        ))

    else:  # PREM-like
        model.append(cake.HomogeneousLayer(
            ztop=0., zbot=15000.,
            m=cake.Material(vp=6800., vs=3900., rho=2900., qp=600., qs=300.)
        ))
        model.append(cake.HomogeneousLayer(
            ztop=15000., zbot=24400.,
            m=cake.Material(vp=6800., vs=3900., rho=2900., qp=600., qs=300.)
        ))
        model.append(cake.HomogeneousLayer(
            ztop=24400., zbot=80000.,
            m=cake.Material(vp=8110., vs=4500., rho=3380., qp=1400., qs=600.)
        ))

    return model


def print_model_summary(model):
    """
    Print a summary of the velocity model.

    Parameters:
    -----------
    model : cake.LayeredModel
        The velocity model
    """
    print("\nVelocity Model Summary:")
    print("-" * 70)
    print(f"{'Depth (km)':<15} {'Vp (km/s)':<12} {'Vs (km/s)':<12} {'Density (g/cm³)':<15}")
    print("-" * 70)

    for layer in model.layers():
        ztop_km = layer.ztop / 1000.
        zbot_km = layer.zbot / 1000.
        vp_km_s = layer.m.vp / 1000.
        vs_km_s = layer.m.vs / 1000.
        rho_g_cm3 = layer.m.rho / 1000.

        print(f"{ztop_km:6.1f}-{zbot_km:6.1f}  "
              f"{vp_km_s:6.2f}       "
              f"{vs_km_s:6.2f}       "
              f"{rho_g_cm3:6.2f}")
    print("-" * 70)


def main():
    """Test velocity model loading"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python velocity_models.py <model_spec>")
        print("\nExamples:")
        print("  python velocity_models.py iasp91")
        print("  python velocity_models.py model.tvel")
        print("  python velocity_models.py custom_model.txt")
        return 1

    model_spec = sys.argv[1]

    try:
        model = load_velocity_model(model_spec)
        print_model_summary(model)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
