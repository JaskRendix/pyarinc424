from __future__ import annotations

import pandas as pd


def decode_arinc_coordinate(coord_str: str) -> float | None:
    """Decode a single ARINC 424 coordinate string into decimal degrees.

    Latitude format: NDDMMSSss (9 chars, e.g., 'N48073012' -> 48°07'30.12" N)
    Longitude format: EDDDMMSSss (10 chars, e.g., 'E013221000' -> 13°22'10.00" E)
    """
    if not isinstance(coord_str, str):
        return None

    coord_str = coord_str.strip()
    if len(coord_str) < 8:
        return None

    hemi = coord_str[0].upper()
    if hemi not in ("N", "S", "E", "W"):
        return None

    try:
        if hemi in ("N", "S"):
            # Latitude: N + DD (2) + MM (2) + SS (2) + ss (rest)
            deg = float(coord_str[1:3])
            min_ = float(coord_str[3:5])
            sec_str = coord_str[5:7]
            frac_str = coord_str[7:]
            sec = float(f"{sec_str}.{frac_str}") if frac_str else float(sec_str)
        else:
            # Longitude: E/W + DDD (3) + MM (2) + SS (2) + ss (rest)
            deg = float(coord_str[1:4])
            min_ = float(coord_str[4:6])
            sec_str = coord_str[6:8]
            frac_str = coord_str[8:]
            sec = float(f"{sec_str}.{frac_str}") if frac_str else float(sec_str)

        decimal = deg + (min_ / 60.0) + (sec / 3600.0)
        if hemi in ("S", "W"):
            decimal = -decimal

        return round(decimal, 6)

    except Exception:
        return None


def decode_magvar(s: str) -> float | None:
    """Decode ARINC 424 Magnetic Variation.

    Supports 5-char tenths-of-degree format (e.g. 'E0125' -> +12.5°),
    legacy minutes format (e.g. 'E01230' -> +12.5°), and True North ('T').
    """
    if not isinstance(s, str):
        return None

    s = s.strip()
    if len(s) < 5:
        return None

    hemi = s[0].upper()
    if hemi not in ("E", "W", "T"):  # T = True North (0.0)
        return None

    if hemi == "T":
        return 0.0

    try:
        if len(s) == 5:
            # ARINC 424 standard: E/W + DDD (degrees) + T (tenths)
            deg = float(s[1:4])
            tenths = float(s[4])
            decimal = deg + (tenths / 10.0)
        else:
            # Legacy minutes format: E/W + DD (deg) + MM (min)
            deg = float(s[1:3])
            min_ = float(s[3:5])
            decimal = deg + (min_ / 60.0)

        return decimal if hemi == "E" else -decimal
    except Exception:
        return None


def decode_frequency(s: str) -> float | None:
    """Decode ARINC 424 frequency fields.

    Handles both kHz integer values and encoded MHz formats common in comms/navaids.
    """
    if not isinstance(s, str):
        return None
    s = s.strip()
    if not s:
        return None
    try:
        val = float(s)
        # If value is large (e.g., > 10000), it's typically encoded in kHz (e.g., 118100 -> 118.1 MHz)
        if val > 10000:
            return round(val / 1000.0, 3)
        return round(val, 3)
    except Exception:
        return None


def decode_elevation(s: str) -> float | None:
    """Decode ARINC 424 elevation/altitude fields.

    Accounts for sign prefixes or specialized surface level indicators.
    """
    if not isinstance(s, str):
        return None
    s = s.strip()
    if not s:
        return None

    sign = 1
    if s.startswith("-") or s.startswith("B"):
        sign = -1
        s = s[1:]
    elif s.startswith("+"):
        s = s[1:]

    try:
        return float(s) * sign
    except Exception:
        return None


def apply_decoders(df: pd.DataFrame) -> pd.DataFrame:
    """Apply coordinate, magnetic variation, frequency, and elevation decoders across matching DataFrame columns."""
    out = df.copy()

    for col in df.columns:
        if col.endswith(("Latitude", "Longitude")):
            decoded = df[col].map(
                lambda v: decode_arinc_coordinate(v) if pd.notna(v) else None
            )
            out[f"{col}_decimal"] = pd.to_numeric(decoded, errors="coerce")

        elif col in ("DynamicMagneticVariation", "MagneticVariation"):
            decoded = df[col].map(lambda v: decode_magvar(v) if pd.notna(v) else None)
            out[f"{col}_decimal"] = pd.to_numeric(decoded, errors="coerce")

        elif col.endswith(("Frequency", "Channel")) or col in (
            "CommsFrequency",
            "NavFrequency",
        ):
            decoded = df[col].map(
                lambda v: decode_frequency(v) if pd.notna(v) else None
            )
            out[f"{col}_decoded"] = pd.to_numeric(decoded, errors="coerce")

        elif col.endswith(("Elevation", "Altitude", "Height")) or col in (
            "StationElevation",
            "AltitudeRestriction",
        ):
            decoded = df[col].map(
                lambda v: decode_elevation(v) if pd.notna(v) else None
            )
            out[f"{col}_decoded"] = pd.to_numeric(decoded, errors="coerce")

    return out
